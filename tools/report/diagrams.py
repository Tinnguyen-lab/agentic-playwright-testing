"""Sơ đồ cho báo cáo (PNG 200dpi). Chạy: python diagrams.py"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.family"] = "DejaVu Sans"
INK, MUTED = "#1f2937", "#6b7280"
AGENT, SERVICE, HUMAN, EXT = "#dbeafe", "#e5e7eb", "#fde68a", "#dcfce7"


def box(ax, x, y, w, h, text, fill, size=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec=INK, lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p, q, text="", style="-|>", color=INK, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=11, color=color, lw=1.0,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls))
    if text:
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.12, text, ha="center", fontsize=7.5, color=MUTED)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def architecture(path):
    fig, ax = canvas(11, 6.2)
    box(ax, 0.3, 5.2, 2.2, 0.7, "Tester / Người duyệt", HUMAN, bold=True)
    box(ax, 3.2, 5.2, 4.6, 0.7, "Giao diện Streamlit (src/ui)", SERVICE, bold=True)
    arrow(ax, (2.5, 5.55), (3.2, 5.55))
    # agents
    names = ["Requirement\nAnalysis Agent", "Test Design\nAgent", "Playwright\nGeneration Agent", "Execution\nAgent", "Repair\nAgent"]
    xs = [0.3, 2.45, 4.6, 6.75, 8.9]
    for x, n in zip(xs, names):
        box(ax, x, 3.2, 1.85, 0.95, n, AGENT, size=8.5, bold=True)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 1.85, 3.67), (b, 3.67))
    arrow(ax, (5.5, 5.2), (5.5, 4.15), "điều phối + cổng duyệt")
    # services
    svc = [("LLM client\n(OpenAI-compatible:\nDeepSeek / LM Studio)", 0.3), ("Boundary analysis\n(BVA tất định)", 2.45),
           ("Locator policy +\ngrounding đa bước", 4.6), ("Script template\n(Jinja2)", 6.75), ("Repair policy +\nself-healing locator", 8.9)]
    for t, x in svc:
        box(ax, x, 1.75, 1.85, 0.95, t, SERVICE, size=7.5)
        arrow(ax, (x + 0.92, 3.2), (x + 0.92, 2.7), style="<|-|>")
    box(ax, 0.3, 0.3, 4.9, 0.85, "Traceability service: REQ → TC → Script → Exec → Repair\n(độ phủ, pass rate, artifact mồ côi)", SERVICE, size=8)
    box(ax, 5.5, 0.3, 2.6, 0.85, "Trình duyệt Chromium\n(Playwright 1.62)", EXT, size=8)
    box(ax, 8.4, 0.3, 2.35, 0.85, "Website đích\n(ứng dụng web thật)", EXT, size=8)
    arrow(ax, (8.1, 0.72), (8.4, 0.72), style="<|-|>")
    arrow(ax, (7.67, 1.75), (6.8, 1.15))
    arrow(ax, (5.52, 1.75), (6.2, 1.15))
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def pipeline(path):
    fig, ax = canvas(11, 3.2)
    steps = [("Tài liệu\nyêu cầu", EXT), ("Requirement\nAgent", AGENT), ("AG-01\nduyệt\nyêu cầu", HUMAN),
             ("Test Design\nAgent + BVA", AGENT), ("AG-02\nduyệt\ntest case", HUMAN), ("Generation\n+ grounding", AGENT),
             ("Execution", AGENT), ("Repair\nproposal", AGENT), ("AG-03..05\nduyệt sửa", HUMAN)]
    w, gap, y = 1.05, 0.165, 1.9
    for i, (t, c) in enumerate(steps):
        x = 0.15 + i * (w + gap)
        box(ax, x, y, w, 1.0, t, c, size=7.2, bold=c == HUMAN)
        if i:
            arrow(ax, (x - gap, y + 0.5), (x, y + 0.5))
    # failure loop
    x_exec = 0.15 + 6 * (w + gap)
    x_last = 0.15 + 8 * (w + gap)
    arrow(ax, (x_last + w / 2, y), (x_exec + w / 2, y), rad=-0.45, color=MUTED, ls="--")
    ax.text((x_last + x_exec + w) / 2, y - 0.85, "được duyệt → chạy lại (ngân sách sửa ≤ 2)", ha="center", fontsize=7.5, color=MUTED)
    ax.text(0.15, 0.15, "Ô vàng = cổng con người quyết định; agent chỉ đề xuất, không tự áp dụng thay đổi.\n"
            "Mỗi artifact mang ID truy vết REQ-xxx → REQ-xxx-TC-yy → script → kết quả → đề xuất sửa.",
            fontsize=8, color=MUTED)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def rq2_protocol(path):
    fig, ax = canvas(11, 4.2)
    box(ax, 0.2, 1.6, 1.9, 1.0, "Catalog 50 target\n(test case + URL\n+ expected_result)", EXT, size=8)
    box(ax, 2.7, 2.75, 2.5, 0.9, "Nhánh none (baseline)\nprompt = test case + URL", AGENT, size=8)
    box(ax, 2.7, 0.55, 2.5, 0.9, "Nhánh aria (DOM-aware)\nprompt + aria snapshot", AGENT, size=8)
    box(ax, 5.8, 1.6, 1.9, 1.0, "LLM sinh\nPlaywrightPlan\n(JSON schema)", SERVICE, size=8)
    box(ax, 8.2, 1.6, 2.6, 1.0, "Render script → chạy thật\n(Chromium headless)\n→ passed / failed / error", SERVICE, size=8)
    arrow(ax, (2.1, 2.3), (2.7, 3.2))
    arrow(ax, (2.1, 1.9), (2.7, 1.0))
    arrow(ax, (5.2, 3.2), (5.8, 2.3))
    arrow(ax, (5.2, 1.0), (5.8, 1.9))
    arrow(ax, (7.7, 2.1), (8.2, 2.1))
    box(ax, 8.2, 3.05, 2.6, 0.75, "Oracle viết tay (cận trên)\nkiểm chứng target khả thi", HUMAN, size=8)
    arrow(ax, (9.5, 3.05), (9.5, 2.6), ls="--", color=MUTED)
    box(ax, 0.2, 3.05, 1.9, 0.75, "Playwright mở URL\n→ aria_snapshot()", EXT, size=7.5)
    arrow(ax, (2.1, 3.3), (3.4, 1.45), color=MUTED, ls="--", rad=-0.2)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    architecture("fig_architecture.png")
    pipeline("fig_pipeline.png")
    rq2_protocol("fig_rq2_protocol.png")
    print("ok")
