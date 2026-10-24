# Rules Learned

- Energy-gated eligibility plus centered activity competition did not improve room reach: 0 across four scales in 2 seeds, matching the parent ablation.
- Small survival and foraging changes (age 69.70 vs 67.85; between-patch foraging 1.887 vs 1.809) did not translate into escaping the first room.
- A 6000-step horizon does not test later learning when the organism dies before reaching the next room; inspect early survival and room transitions first.
- Energy-dependent sigmoid speed (gain 7, midpoint energy 0.5) also scored 0 rooms at all four scales in 2 seeds; mean age 64.01 and between-patch foraging 1.672, below the prior candidate values. Smooth energy throttling alone did not rescue the life.
- The scale sweep gave identical means at 302, 1k, 10k and 100k units; current behavior is limited before brain size can matter.
- A two-seed organism run of `odkrywca_habituation_flow` scored 0.1797 (rooms_reached 0.1797, foraging 3.168, mean_age 165.2); its gain-zero ablation scored 0.1719 (0.1719, 3.246, 155.4). The small room difference does not establish a habituation benefit, and the primary foraging metric was slightly lower.
- Reducing habituation_gain from 2.0 to 0.4 scored 0.1719, foraging 3.000, and age 159.4 (same four-scale, two-seed organism protocol); weaker color habituation did not improve the primary metric over gain=2.0 or the gain-zero ablation. Scale means remained identical.
