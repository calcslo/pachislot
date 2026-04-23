import sys
import os
import platform

def check_environment():
    print("="*30)
    print("🐍 Python 実行環境チェック")
    print("="*30)

    # 1. 仮想環境の確認
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✅ 仮想環境アクティベート中: {venv_path}")
    else:
        print("❌ 仮想環境が認識されていません（素のPythonです）")

    # 2. 実行ファイルのパス確認
    print(f"📍 実行パス: {sys.executable}")

    # 3. ライブラリのインポートテスト (スロット解析等で使用するもの)
    print("\n📦 ライブラリ確認:")
    libraries = ['pandas', 'numpy', 'selenium', 'playwright']
    for lib in libraries:
        try:
            __import__(lib)
            print(f"  - {lib:12}: OK")
        except ImportError:
            print(f"  - {lib:12}: 未インストール")

    # 4. GPU (CUDA) の簡易チェック
    # あなたの RTX 5070 Ti が Python から見えるか確認します
    print("\n🎮 ハードウェア確認:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  - GPU (CUDA)  : 使用可能 ({torch.cuda.get_device_name(0)})")
        else:
            print("  - GPU (CUDA)  : 認識されていますが、CUDAが利用不可です")
    except ImportError:
        print("  - torch が未インストールのたGPU確認をスキップします")

    print("\n" + "="*30)
    print("診断完了")

if __name__ == "__main__":
    check_environment()