# Handoff

- Katalog roboczy: `/opt/dlami/nvme/genesis_archive/archeology`.
- Nie zapisuj w `/opt/dlami/nvme/genesis/` ani `/opt/dlami/nvme/dataset/`; nie pisz do zespołu agentów.
- Źródła: `/opt/dlami/nvme/genesis_archive/2026-10-23_reset/`.
- `families.tsv` ma 122 wpisy; `sandbox/disqualified.tsv` jest pusty.
- Potwierdzony baseline `_baseline_gpu_online`, 10k kroków: jakość 1e3/1e4/1e5 `0.9422/0/0`, nachylenie rozmiaru `-0.141808`, stan 1e5 `400000 B`.
- Przeniesiono `inertial_channel_dynamics` do lokalnego `candidates/`; GPU zgodne z CPU, max error `0.0`.
- Jego wynik 1e3/1e4/1e5 `0.9528/0.9994/0.9298`, nachylenie rozmiaru `-0.003459`, nachylenie czasu `0`, wykładnik stanu `1`.
- Rzeczywista pamięć GPU szczytowa: baseline `10.71 MiB`, bezwładność `11.09 MiB`; stan zgłoszony obu przy 1e5: `400000 B`.
- Sprawdź `mechanisms.tsv`, `results.tsv`, `REPORT.md`; raport jest celowo niepełny i nie rozstrzyga całości pytania.
- Pozostało: pogrupować rodziny po równoważności reguł i opisach, wybrać 20–40 mechanizmów, przenieść/przetestować bądź uzasadnić brak wiernego portu.
- Każdy GPU run wykonuj kolejno: `nice -n 15 /opt/dlami/nvme/genesis/.venv/bin/python sandbox/judge.py candidates/<name> --gpu`.
- Porównuj z baseline'em na tych samych ustawieniach; domyślnie jest 10k kroków i skale 1e3/1e4/1e5.
