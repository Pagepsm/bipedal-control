# 地形を保存して同じ条件を再現する

Bipedal Terrain Studio v0.9では、地形の高さ・環境seed・制御器を別々に選びます。ブラウザが受け付けた線をPythonで等間隔の高さに変換し、Gymnasiumの歩行環境へ渡します。ブラウザ側では物理計算を繰り返さず、記録された動きを描画します。

## モデルを使わずに試す

Python 3.11以降とPowerShellで、リポジトリのルートから次を実行してください。最後に表示される値は、地形データの内容から計算したSHA-256です。

~~~powershell
$env:PYTHONPATH = "src;studio"
python -m unittest discover -s tests -v
python -c "import json; from pathlib import Path; from robust_bipedal.terrain_geometry import TerrainProfile; p=TerrainProfile.from_data(json.loads(Path('examples/rolling_hills.heightfield.json').read_text())); print(len(p.world_points()), p.terrain_sha256)"
~~~

- [地形形式](../schemas/terrain.heightfield.v1.schema.json)では、手描きの線を物理空間の高さに変換します。先頭20点を平坦に保ち、同じ高さの列から同じ識別値を計算します。
- [保存処理](../studio/user_library.py)は名前とデータを分け、保存先には自動生成したIDを使います。一時ファイルへの書込み後に置き換え、読み戻すときに地形の識別値を照合します。[保存場所の切替](../studio/app_paths.py)とともにStudio v0.9から収録しました。
- このリポジトリで実行できる例は地形処理です。デスクトップアプリの実行ファイルと学習済みモデルは配布していません。

## 使用技術とクレジット

物理環境はGymnasiumのBipedalWalkerとBox2D、方策の比較にはPPOを使用しています。外部のTQC参照モデルはRL Baselines3 Zoo系の配布物です。作者・モデル情報は[配布元のモデルカード](https://huggingface.co/sb3/tqc-BipedalWalkerHardcore-v3)をご覧ください。
