# main.py — PBS Editor launcher
# 役割：gui_app.App を立ち上げるだけのエントリポイント

import sys

def _ensure_pyver():
    # Python 3.8+ 推奨（f文字列や型ヒントなどの都合）
    if sys.version_info < (3, 8):
        print(f"[Error] Python 3.8 以上が必要です（検出: {sys.version.split()[0]}）。")
        sys.exit(1)

def _run():
    _ensure_pyver()
    try:
        from gui_app import App
    except ModuleNotFoundError as e:
        print("[Error] 必要なファイルが見つかりません。プロジェクト構成を確認してください。")
        print(" - 必要: gui_app.py, pbs_utils.py, widgets/rows.py, widgets/moves_dialog.py")
        print(f" 詳細: {e}")
        sys.exit(1)
    except Exception as e:
        print("[Error] gui_app の読み込み中に想定外のエラーが発生しました。")
        print(e)
        sys.exit(1)

    try:
        app = App()
        app.mainloop()
    except Exception as e:
        # Tkinter 初期化や実行中の例外を捕捉
        print("[Error] アプリ実行時にエラーが発生しました。")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    _run()
