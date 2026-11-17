#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
for source_name in NUE_PCSE-Gym pcse; do
    if [[ -e "$source_name" ]]; then
        printf 'Refusing to replace existing source directory: %s\n' "$source_name" >&2
        exit 1
    fi
done
nue_commit="$(python3 -c 'import json; print(json.load(open("reports/asset-receipt.json"))["repo_commit"])')"
pcse_commit="$(python3 -c 'import json; print(json.load(open("reports/asset-receipt.json"))["pcse_commit"])')"
git clone https://github.com/WUR-AI/NUE_PCSE-Gym.git NUE_PCSE-Gym
git -C NUE_PCSE-Gym checkout --detach "$nue_commit"
git -C NUE_PCSE-Gym apply ../reports/nue-compat.patch
git clone https://github.com/ajwdewit/pcse.git pcse
git -C pcse checkout --detach "$pcse_commit"
git -C pcse apply ../reports/pcse-path.patch
mkdir -p NUE_PCSE-Gym/pcse_gym/utils/weather_utils/random_weather_csv
ln -s ../../../../../data/52.57-5.63_random_weather.csv NUE_PCSE-Gym/pcse_gym/utils/weather_utils/random_weather_csv/52.57-5.63_random_weather.csv

python3 - <<'PYFIXTURE'
import json,pathlib,urllib.request,hashlib
for item in json.load(open('reports/restored-test-fixtures.json')):
    if item['status'] != 200:
        continue
    content=urllib.request.urlopen(item['url'],timeout=40).read()
    assert len(content)==item['bytes']
    if item.get('sha256'):
        assert hashlib.sha256(content).hexdigest()==item['sha256']
    name=item['url'].rsplit('/',1)[-1]
    pathlib.Path('NUE_PCSE-Gym/tests',name).write_bytes(content)
PYFIXTURE
