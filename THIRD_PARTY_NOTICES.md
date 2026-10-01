# Third-party components

新規教材コードはMIT。以下をMITへ再ライセンスするものではありません。

| Component | Pin | Upstream license / source |
|---|---|---|
| MuJoCo | 3.3.7 | Apache-2.0; https://github.com/google-deepmind/mujoco |
| mujoco-menagerie Python package | 2026.9.0 | Apache-2.0; https://pypi.org/project/mujoco-menagerie/2026.9.0/ |
| unitree_go2 model | oid `98d14ab27a56c3623e29d852a997a422bbfefa19` | BSD-3-Clause; https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_go2 |

固定パッケージのregistryが指すGo2 archive SHA-256:
`e1498c79634a264a069d313dd3ddb8fab881007f67488e206701bdc559d929d1`。
これはモデルサブツリーのoidです。GitHub全体のcommit SHAではありません。

ダウンロードしたモデルのディレクトリにある`LICENSE`がモデルの正式な条件です。
キャッシュをオフライン配布する場合はモデルのディレクトリ全体とLICENSEを保持してください。
NumPy、Matplotlibなど他の依存にもそれぞれのライセンスが適用されます。

## Introduction to Autonomous Robots

授業ではNikolaus Correll、Bradley Hayes、Christoffer Heckman、Alessandro Roncone著
*Introduction to Autonomous Robots: Mechanisms, Sensors, Actuators, and Algorithms* を使用します。
教科書のPDFと原稿はこのリポジトリに含めていません。
[書籍の公式原稿](https://github.com/Introduction-to-Autonomous-Robots/Introduction-to-Autonomous-Robots)には別のライセンスが適用されます。
