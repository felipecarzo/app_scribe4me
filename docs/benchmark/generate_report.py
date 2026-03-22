"""
Gerador do relatório MOT-05-report.md

Lê rust_results.json e python_results.json e gera comparativo Markdown.

Executar (do diretório raiz do projeto):
    python docs/benchmark/generate_report.py
"""

import json
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path(__file__).parent / "results"
REPORT_PATH = RESULTS_DIR / "MOT-05-report.md"


def load(name):
    path = RESULTS_DIR / name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(val, decimals=1, suffix=""):
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.{decimals}f}{suffix}"
    return str(val)


def pct(val):
    if val is None:
        return "—"
    return f"{val * 100:.1f}%"


def delta(rust_val, py_val, higher_is_better=True, suffix="", decimals=1):
    """Calcula delta Rust - Python com sinal de direção."""
    if rust_val is None or py_val is None:
        return "—"
    d = rust_val - py_val
    sign = "+" if d > 0 else ""
    better = (d > 0) == higher_is_better
    marker = "✓" if better else "✗"
    return f"{sign}{d:.{decimals}f}{suffix} {marker}"


def delta_pct(rust_val, py_val, higher_is_better=True):
    if rust_val is None or py_val is None:
        return "—"
    d = (rust_val - py_val) * 100
    sign = "+" if d > 0 else ""
    better = (d > 0) == higher_is_better
    marker = "✓" if better else "✗"
    return f"{sign}{d:.1f}pp {marker}"


def find_direction(data, src, tgt):
    direction = f"{src}→{tgt}"
    for d in data.get("by_direction", []):
        if d.get("direction") == direction:
            return d
    return None


def failures(data, threshold=0.75):
    """Lista resultados com quality_score < threshold."""
    results = data.get("all_results", [])
    return [r for r in results if r.get("quality_score", 1.0) < threshold]


def domain_summary(data):
    """Agrega pass_rate por domínio."""
    from collections import defaultdict
    domain_map = defaultdict(lambda: {"total": 0, "passed": 0, "scores": []})
    for r in data.get("all_results", []):
        d = r.get("domain", "?")
        domain_map[d]["total"] += 1
        if r.get("passed", False):
            domain_map[d]["passed"] += 1
        domain_map[d]["scores"].append(r.get("quality_score", 0.0))
    result = {}
    for d, v in domain_map.items():
        n = v["total"]
        result[d] = {
            "pass_rate": v["passed"] / n if n else 0,
            "mean_score": sum(v["scores"]) / n if n else 0,
            "count": n,
        }
    return result


def generate():
    rust = load("rust_results.json")
    py = load("python_results.json")

    if rust is None and py is None:
        print("Nenhum resultado encontrado. Rode os benchmarks primeiro.")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append("# MOT-05 — Relatório de Benchmark: Motor Rust vs Python")
    lines.append(f"\n**Gerado em:** {now}  ")
    lines.append(f"**Corpus:** {rust['corpus_size'] if rust else py['corpus_size']} frases × 6 direções (PT/EN/ZH)")

    # Sumário executivo
    lines.append("\n## Sumário Executivo\n")
    if rust and py:
        rust_quality = rust["global"]["mean_quality_score"]
        py_quality = py["global"]["mean_quality_score"]
        rust_latency = rust["global"]["mean_latency_ms"]
        py_latency = py["global"]["mean_latency_ms"]
        rust_pass = rust["global"]["pass_rate"]
        py_pass = py["global"]["pass_rate"]

        quality_winner = "Rust" if rust_quality >= py_quality else "Python"
        latency_winner = "Rust" if rust_latency <= py_latency else "Python"
        lines.append(
            f"- **Qualidade**: {quality_winner} apresenta maior quality score médio "
            f"(Rust={rust_quality:.3f}, Python={py_quality:.3f})"
        )
        lines.append(
            f"- **Latência**: {latency_winner} é mais rápido "
            f"(Rust={rust_latency:.0f}ms, Python={py_latency:.0f}ms média por frase)"
        )
        lines.append(
            f"- **Pass rate**: Rust={pct(rust_pass)}, Python={pct(py_pass)} "
            f"(threshold ≥ 0.75)"
        )
    elif rust:
        lines.append(f"- Apenas resultados Rust disponíveis. Quality score médio: {rust['global']['mean_quality_score']:.3f}")
    else:
        lines.append(f"- Apenas resultados Python disponíveis. Quality score médio: {py['global']['mean_quality_score']:.3f}")

    # Condições de teste
    lines.append("\n## Condições de Teste\n")
    lines.append("| Aspecto | Rust | Python |")
    lines.append("|---|---|---|")

    rust_decoder = rust["model_decoder"] if rust else "—"
    rust_encoder = rust["model_encoder"] if rust else "—"
    py_decoder = py["model_decoder"] if py else "—"
    py_encoder = py["model_encoder"] if py else "—"

    lines.append(f"| Decoder | {rust_decoder} | {py_decoder} |")
    lines.append(f"| Encoder | {rust_encoder} | {py_encoder} |")
    lines.append(f"| Quality threshold | 0.75 | 0.75 |")
    lines.append(f"| Warn threshold | 0.60 | 0.60 |")

    # Performance global
    lines.append("\n## Performance — Latência\n")
    lines.append("| Direção | Rust P50 | Rust P90 | Python P50 | Python P90 | Δ P50 |")
    lines.append("|---|---|---|---|---|---|")

    directions = [("pt","en"),("pt","zh"),("en","pt"),("en","zh"),("zh","pt"),("zh","en")]
    for src, tgt in directions:
        rd = find_direction(rust, src, tgt) if rust else None
        pd = find_direction(py, src, tgt) if py else None
        r_p50 = rd["latency_p50_ms"] if rd else None
        r_p90 = rd["latency_p90_ms"] if rd else None
        p_p50 = pd["latency_p50_ms"] if pd else None
        p_p90 = pd["latency_p90_ms"] if pd else None
        d_p50 = delta(r_p50, p_p50, higher_is_better=False, suffix="ms")
        lines.append(
            f"| {src}→{tgt} | {fmt(r_p50,0,'ms')} | {fmt(r_p90,0,'ms')} "
            f"| {fmt(p_p50,0,'ms')} | {fmt(p_p90,0,'ms')} | {d_p50} |"
        )

    # Qualidade global
    lines.append("\n## Qualidade — Score Semântico\n")
    lines.append("| Direção | Rust Score | Rust Pass | Python Score | Python Pass | Δ Score |")
    lines.append("|---|---|---|---|---|---|")

    for src, tgt in directions:
        rd = find_direction(rust, src, tgt) if rust else None
        pd = find_direction(py, src, tgt) if py else None
        r_score = rd["mean_quality_score"] if rd else None
        r_pass = rd["pass_rate"] if rd else None
        p_score = pd["mean_quality_score"] if pd else None
        p_pass = pd["pass_rate"] if pd else None
        d_score = delta(r_score, p_score, higher_is_better=True, suffix="", decimals=3)
        lines.append(
            f"| {src}→{tgt} | {fmt(r_score,3)} | {pct(r_pass)} "
            f"| {fmt(p_score,3)} | {pct(p_pass)} | {d_score} |"
        )

    # Por domínio
    lines.append("\n## Qualidade por Domínio\n")
    lines.append("| Domínio | Rust Pass Rate | Rust Score | Python Pass Rate | Python Score |")
    lines.append("|---|---|---|---|---|")

    domains = ["conversacao", "saude", "viagem", "tecnico", "negocios"]
    rust_dom = domain_summary(rust) if rust else {}
    py_dom = domain_summary(py) if py else {}

    for d in domains:
        rd = rust_dom.get(d, {})
        pd = py_dom.get(d, {})
        lines.append(
            f"| {d} | {pct(rd.get('pass_rate'))} | {fmt(rd.get('mean_score'),3)} "
            f"| {pct(pd.get('pass_rate'))} | {fmt(pd.get('mean_score'),3)} |"
        )

    # Falhas notáveis
    lines.append("\n## Casos de Falha Notáveis\n")

    for engine_name, data in [("Rust", rust), ("Python", py)]:
        if data is None:
            continue
        fails = failures(data)
        if not fails:
            lines.append(f"### {engine_name}: nenhuma falha (quality < 0.75)\n")
        else:
            lines.append(f"### {engine_name}: {len(fails)} tradução(ões) com quality < 0.75\n")
            lines.append("| ID | Direção | Score | Fonte | Tradução |")
            lines.append("|---|---|---|---|---|")
            for r in sorted(fails, key=lambda x: x.get("quality_score", 0)):
                score = r.get("quality_score", 0)
                src_txt = r.get("source", "")[:60]
                tgt_txt = r.get("translation", "")[:60]
                direction = f"{r.get('src_lang','?')}→{r.get('tgt_lang','?')}"
                crit = " ⚠" if r.get("critically_low", False) else ""
                lines.append(f"| {r['id']} | {direction} | {score:.3f}{crit} | {src_txt} | {tgt_txt} |")
            lines.append("")

    # Critically low
    lines.append("\n## Critically Low (score < 0.60) — Análise\n")
    for engine_name, data in [("Rust", rust), ("Python", py)]:
        if data is None:
            continue
        crits = [r for r in data.get("all_results", []) if r.get("critically_low", False)]
        rate = data["global"]["critically_low_rate"]
        lines.append(f"**{engine_name}**: {len(crits)} ocorrências ({rate*100:.1f}%)")
        if crits:
            for r in crits:
                lines.append(
                    f"  - [{r['id']}] {r.get('src_lang','?')}→{r.get('tgt_lang','?')} "
                    f"score={r.get('quality_score',0):.3f}: `{r.get('source','')[:50]}` → `{r.get('translation','')[:50]}`"
                )
        lines.append("")

    # Conclusão
    lines.append("## Conclusão\n")
    if rust and py:
        rust_q = rust["global"]["mean_quality_score"]
        py_q = py["global"]["mean_quality_score"]
        rust_l = rust["global"]["mean_latency_ms"]
        py_l = py["global"]["mean_latency_ms"]

        lines.append("### Qualidade")
        if rust_q >= py_q - 0.02:
            lines.append(
                f"O motor Rust apresenta qualidade semântica comparável ao Python "
                f"({rust_q:.3f} vs {py_q:.3f}). A diferença de {abs(rust_q-py_q):.3f} "
                f"é atribuída ao greedy decoding (Rust) vs beam_size=4 (Python)."
            )
        else:
            lines.append(
                f"O motor Python apresenta qualidade superior ({py_q:.3f} vs {rust_q:.3f}). "
                f"O gap de {py_q-rust_q:.3f} sugere que beam search deve ser avaliado para o decoder Rust (MOT-06+)."
            )

        lines.append("\n### Performance")
        speedup = py_l / rust_l if rust_l > 0 else 0
        if speedup > 1:
            lines.append(f"O motor Rust é **{speedup:.1f}x mais rápido** que o Python em CPU (P50: {rust_l:.0f}ms vs {py_l:.0f}ms).")
        else:
            lines.append(f"O Python apresentou latência menor neste hardware ({py_l:.0f}ms vs {rust_l:.0f}ms). Investigar overhead do ort vs ctranslate2.")

        lines.append("\n### Recomendações")
        lines.append("- [ ] Se gap de qualidade > 0.05 em PT→ZH ou ZH→*, avaliar beam_size=2 no decoder Rust")
        lines.append("- [ ] Se critically_low > 5% em qualquer direção, investigar tokenização NLLB para esse par")
        lines.append("- [ ] Atualizar QUALITY_THRESHOLD por direção se houver assimetria sistemática")
    else:
        lines.append("Execute ambos os benchmarks para comparação completa.")

    # Rodapé
    lines.append(f"\n---\n*Gerado automaticamente por `generate_report.py` em {now}*")

    report = "\n".join(lines)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Relatório gerado em: {REPORT_PATH}")
    print(f"Linhas: {len(lines)}")


if __name__ == "__main__":
    generate()
