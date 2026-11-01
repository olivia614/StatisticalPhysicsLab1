import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from src.microstates import enumerate_coins, time_generator
from src.combinatorics import get_distribution, prob_k, cumulative_prob
from src.thermodynamics import get_team_N, delta_entropy, waiting_time, likelihood_ratio

NIAS = [100400036, 100400045, 100400060, 100400075]


def plot_distributions(save_dir: Path):
    save_dir.mkdir(parents=True, exist_ok=True)
    N_list = [20, 50, 80, 100]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
    markers = ["o", "s", "^", "d"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    for N, col, mk in zip(N_list, colors, markers):
        k, ln_w, p_k = get_distribution(N)
        # Convert natural log ln(Omega) to base-10 log10(Omega) for clean plotting
        omega_vals = 10.0 ** (ln_w / np.log(10.0))

        ax1.plot(k, p_k, label=f"N = {N}", color=col, marker=mk, markersize=3.5, lw=1.2)
        ax2.plot(k, omega_vals, label=f"N = {N}", color=col, marker=mk, markersize=3.5, lw=1.2)

    # Panel (a): Linear probability bell curves
    ax1.set_title("(a) Probability Distribution $P_k = \\Omega(N,k)/2^N$")
    ax1.set_xlabel("Number of heads $k$")
    ax1.set_ylabel("Probability $P_k$")
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 0.20)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Panel (b): Unobstructed log-scale multiplicity with headroom for the legend
    ax2.set_title("(b) Macrostate Multiplicity $\\Omega(N,k)$")
    ax2.set_xlabel("Number of heads $k$")
    ax2.set_ylabel("Multiplicity $\\Omega(N,k)$")
    ax2.set_yscale("log")
    ax2.set_xlim(0, 100)
    ax2.set_ylim(1e0, 1e37)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", ncol=2, fontsize=9)

    fig.tight_layout()
    out_file = save_dir / "macrostate_distributions.pdf"
    fig.savefig(out_file, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure to {out_file}")


def main():
    # Part 1: Microstates for N = 7
    print("Part 1a: N = 7 Enumeration")
    n7_data = enumerate_coins(7)
    for k, states in n7_data.items():
        print(f"{k} heads, {7-k} tails: {len(states)} microstates")

    print("\n Part 1b: Generator Timing Test")
    for n_test in [20, 22, 24]:
        total, dt = time_generator(n_test)
        print(f"N = {n_test}: {total} states in {dt:.4f} s")

    # Part 1c: Plot distributions for N = 20, 50, 80, 100
    print("\n Part 1c: Plotting Macrostate Distributions")
    plot_distributions(Path("report/figures"))

    # Part 2: Probabilities and Entropy for N = 100 + M
    M_exact, M, N = get_team_N(NIAS)
    half = N // 2
    print(f"\n--- Part 2: Results for N = 100 + M = {N} (M = {M_exact:.2f} -> {M}) ---")
    print(f"Total microstates 2^{N} = {2.0**N:.4e}")

    # 2a & 2b
    p30 = prob_k(N, 30)
    p_max = prob_k(N, half)
    print(f"a) P(k=30) = {p30:.4e} (Omega = {math.comb(N, 30):.4e})")
    print(f"b) P(k={half}) = {p_max:.4e} (Omega = {math.comb(N, half):.4e})")

    # 2c & 2d
    cp_10 = cumulative_prob(N, half - 10, half + 10)
    cp_20 = cumulative_prob(N, half - 20, half + 20)
    print(f"c) Cumulative P[{half-10}, {half+10}] = {cp_10:.6f} ({cp_10*100:.4f}%)")
    print(f"d) Cumulative P[{half-20}, {half+20}] = {cp_20:.6f} ({cp_20*100:.4f}%)")

    # 2e, 2f, 2g
    ds_e_kb, ds_e = delta_entropy(N, half + 25, half)
    ds_f_kb, ds_f = delta_entropy(N, half + 10, half)
    ds_g_kb, ds_g = delta_entropy(N, half, 20)
    print(f"e) Delta S({half+25}, {half}): {ds_e_kb:+.4f} k_B  ({ds_e:+.4e} J/K)")
    print(f"f) Delta S({half+10}, {half}): {ds_f_kb:+.4f} k_B  ({ds_f:+.4e} J/K)")
    print(f"g) Delta S({half}, 20): {ds_g_kb:+.4f} k_B  ({ds_g:+.4e} J/K)")

    # 2h
    t_sec, t_yr = waiting_time(N, 8)
    print(f"h) Waiting time for k=8 heads: {t_sec:.4e} s ({t_yr:.4e} years)")

    # 2i
    r_m_minus = likelihood_ratio(N, half, M - 10)
    r_m_plus = likelihood_ratio(N, half, M + 10)
    r_half_10 = likelihood_ratio(N, half, half + 10)
    print(f"i) Ratio P({half}) / P(M-10={M-10}): {r_m_minus:.4e}")
    print(f"   Ratio P({half}) / P(M+10={M+10}): {r_m_plus:.4f}")
    print(f"   Ratio P({half}) / P(N/2+-10={half+10}): {r_half_10:.4f}")


if __name__ == "__main__":
    main()
