"""
MOT-05 — Benchmark motor Python (legacy NLLB-200)
Corpus: 60 frases, 5 domínios, PT/EN/ZH — 6 direções = 360 traduções

Executar (do diretório raiz do projeto):
    python docs/benchmark/benchmark_python.py

Resultados gravados em: docs/benchmark/results/python_results.json
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent  # app_ayvu/
LEGACY_DIR = ROOT / "legacy"
CORPUS_PATH = Path(__file__).parent / "corpus.json"
RESULTS_DIR = Path(__file__).parent / "results"

sys.path.insert(0, str(LEGACY_DIR))

QUALITY_THRESHOLD = 0.75
WARN_THRESHOLD = 0.60


# ── Carregamento dos modelos ──────────────────────────────────────────────

def load_translator():
    """Carrega o pipeline NLLB-200 em CPU float32 (modo padronizado para benchmark)."""
    try:
        from translation_engine import TranslationPipeline
        print("Carregando TranslationPipeline (CPU float32)...")
        pipeline = TranslationPipeline(device="cpu", compute_type="float32")
        print("Pipeline carregado.")
        return pipeline
    except Exception as e:
        print(f"ERRO ao carregar TranslationPipeline: {e}")
        print("Tentando fallback com CTranslate2 direto...")
        return load_translator_direct()


def load_translator_direct():
    """Fallback: carrega NLLB-200 diretamente via CTranslate2."""
    import ctranslate2
    import sentencepiece as spm

    model_path = LEGACY_DIR / "models" / "nllb-200-distilled-600M-ct2"
    spm_path = LEGACY_DIR / "models" / "flores200_sacrebleu_tokenizer_spm.model"

    if not model_path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

    translator = ctranslate2.Translator(str(model_path), device="cpu", compute_type="float32")
    sp = spm.SentencePieceProcessor()
    sp.Load(str(spm_path))
    return {"translator": translator, "sp": sp, "type": "direct"}


def load_embedder():
    """Carrega modelo de embedding multilíngue para quality score."""
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    import numpy as np
    print("Carregando sentence-transformers para quality score...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print("Embedder carregado.")
    return model, cos_sim, np


# ── Tradução ──────────────────────────────────────────────────────────────

NLLB_CODES = {
    "pt": "por_Latn",
    "en": "eng_Latn",
    "zh": "zho_Hans",
}


def translate_pipeline(pipeline, text, src_lang, tgt_lang):
    """Traduz via TranslationPipeline do legacy."""
    result = pipeline.translate(text, src_lang, tgt_lang)
    if isinstance(result, dict):
        return result.get("translated", str(result))
    return str(result)


def translate_direct(ctx, text, src_lang, tgt_lang):
    """Traduz via CTranslate2 direto (fallback)."""
    sp = ctx["sp"]
    translator = ctx["translator"]
    src_code = NLLB_CODES[src_lang]
    tgt_code = NLLB_CODES[tgt_lang]

    tokens = sp.EncodeAsPieces(text)
    tokens = [src_code] + tokens
    results = translator.translate_batch(
        [tokens],
        target_prefix=[[tgt_code]],
        beam_size=4,
        max_decoding_length=512,
    )
    output_tokens = results[0].hypotheses[0][1:]  # remove tgt_code prefix
    return sp.DecodePieces(output_tokens)


def do_translate(ctx, text, src_lang, tgt_lang):
    if isinstance(ctx, dict) and ctx.get("type") == "direct":
        return translate_direct(ctx, text, src_lang, tgt_lang)
    return translate_pipeline(ctx, text, src_lang, tgt_lang)


# ── Quality score ─────────────────────────────────────────────────────────

def quality_score(embedder, cos_sim_fn, np, source, translation):
    """Computa cosine similarity cross-lingual entre source e translation."""
    embs = embedder.encode([source, translation])
    score = float(cos_sim_fn([embs[0]], [embs[1]])[0][0])
    return {
        "score": score,
        "passed": score >= QUALITY_THRESHOLD,
        "critically_low": score < WARN_THRESHOLD,
    }


# ── Percentis ─────────────────────────────────────────────────────────────

def percentile(data, p):
    if not data:
        return 0.0
    s = sorted(data)
    idx = max(0, min(int(len(s) * p / 100), len(s) - 1))
    return s[idx]


# ── Benchmark principal ───────────────────────────────────────────────────

def run_corpus(ctx, embedder, cos_fn, np, pairs, src_lang, tgt_lang):
    results = []
    lang_field = src_lang
    direction = f"{src_lang}→{tgt_lang}"

    for pair in pairs:
        pid = pair["id"]
        domain = pair["domain"]
        source = pair.get(lang_field, "")
        if not source:
            print(f"  [{pid}] SKIP: campo '{lang_field}' ausente")
            continue

        t0 = time.perf_counter()
        try:
            translation = do_translate(ctx, source, src_lang, tgt_lang)
            error = None
        except Exception as e:
            translation = f"ERRO: {e}"
            error = str(e)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        if translation.startswith("ERRO:"):
            q = {"score": 0.0, "passed": False, "critically_low": True}
        else:
            q = quality_score(embedder, cos_fn, np, source, translation)

        flag = " [CRIT]" if q["critically_low"] else (" [FAIL]" if not q["passed"] else "")
        print(f"  [{pid}] {latency_ms:.0f}ms | score={q['score']:.3f}{flag}")
        print(f"    src: {source}")
        print(f"    tgt: {translation}")

        results.append({
            "id": pid,
            "domain": domain,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "source": source,
            "translation": translation,
            "quality_score": q["score"],
            "passed": q["passed"],
            "critically_low": q["critically_low"],
            "latency_ms": latency_ms,
            "error": error,
        })

    return results


def aggregate(results, src, tgt):
    subset = [r for r in results if r["src_lang"] == src and r["tgt_lang"] == tgt]
    if not subset:
        return {"direction": f"{src}→{tgt}", "count": 0}

    latencies = sorted(r["latency_ms"] for r in subset)
    scores = [r["quality_score"] for r in subset]
    pass_count = sum(1 for r in subset if r["passed"])
    crit_count = sum(1 for r in subset if r["critically_low"])
    n = len(subset)

    return {
        "direction": f"{src}→{tgt}",
        "count": n,
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p90_ms": percentile(latencies, 90),
        "latency_p99_ms": percentile(latencies, 99),
        "latency_mean_ms": sum(latencies) / n,
        "mean_quality_score": sum(scores) / n,
        "pass_rate": pass_count / n,
        "critically_low_rate": crit_count / n,
        "results": subset,
    }


def main():
    with open(CORPUS_PATH, encoding="utf-8") as f:
        corpus = json.load(f)
    pairs = corpus["pairs"]

    print(f"\n=== MOT-05 Benchmark — Motor Python (legacy) ===")
    print(f"Corpus: {len(pairs)} frases × 6 direções = {len(pairs) * 6} traduções")

    # Carrega modelos
    ctx = load_translator()
    embedder, cos_fn, np = load_embedder()

    # Warm-up
    print("\nIniciando warm-up...")
    _ = do_translate(ctx, "Olá", "pt", "en")
    print("Warm-up concluído. Iniciando medições...\n")

    directions = [
        ("pt", "en"), ("pt", "zh"),
        ("en", "pt"), ("en", "zh"),
        ("zh", "pt"), ("zh", "en"),
    ]

    all_results = []
    total_latency = 0.0

    for src, tgt in directions:
        print(f"Direção {src}→{tgt}:")
        results = run_corpus(ctx, embedder, cos_fn, np, pairs, src, tgt)
        all_results.extend(results)
        total_latency += sum(r["latency_ms"] for r in results)
        print()

    # Agrega
    summaries = [aggregate(all_results, src, tgt) for src, tgt in directions]

    n = len(all_results)
    pass_total = sum(1 for r in all_results if r["passed"])
    crit_total = sum(1 for r in all_results if r["critically_low"])
    mean_quality = sum(r["quality_score"] for r in all_results) / n if n else 0

    print("=== Resumo Global ===")
    print(f"Total de traduções: {n}")
    print(f"Tempo total: {total_latency:.0f}ms")
    print(f"Latência média: {total_latency / n:.0f}ms")
    print(f"Quality score médio: {mean_quality:.4f}")
    print(f"Pass rate (>=0.75): {pass_total / n * 100:.1f}%")
    print(f"Critically low (<0.60): {crit_total / n * 100:.1f}%")

    print("\nPor direção:")
    for s in summaries:
        if s["count"] == 0:
            continue
        print(
            f"  {s['direction']} | P50={s['latency_p50_ms']:.0f}ms P90={s['latency_p90_ms']:.0f}ms "
            f"| quality={s['mean_quality_score']:.3f} | pass={s['pass_rate']*100:.1f}% "
            f"| crit={s['critically_low_rate']*100:.1f}%"
        )

    # Serializa
    output = {
        "engine": "python",
        "engine_version": "legacy-v6.0",
        "model_decoder": "nllb-200-distilled-600M-ct2 (ctranslate2, beam_size=4, cpu float32)",
        "model_encoder": "paraphrase-multilingual-MiniLM-L12-v2 (sentence-transformers)",
        "corpus_version": corpus["version"],
        "corpus_size": len(pairs),
        "total_translations": n,
        "quality_threshold": QUALITY_THRESHOLD,
        "warn_threshold": WARN_THRESHOLD,
        "global": {
            "mean_quality_score": mean_quality,
            "pass_rate": pass_total / n if n else 0,
            "critically_low_rate": crit_total / n if n else 0,
            "mean_latency_ms": total_latency / n if n else 0,
        },
        "by_direction": summaries,
        "all_results": all_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "python_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResultados gravados em: {out_path}")


if __name__ == "__main__":
    main()
