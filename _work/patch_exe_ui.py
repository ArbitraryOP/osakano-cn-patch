"""Translate exe-hardcoded Japanese UI strings to GBK Chinese (equal-length, in place).
Patches E:\\game\\幼なじみな彼女\\osakano.exe (== E:\\game\\cn hardlink) then syncs build\\.
Skips font character-map tables, font names, debug/CPU/OS strings.
Each replacement is encoded cp936 and must fit within the original cp932 byte length;
the run is null-terminated, so we pad the remaining bytes (up to the original NUL) with 0x00.
"""
import io, sys, os
sys.stdout = io.open(r"E:\game\_work\uipatch_out.txt", "w", encoding="utf-8")

EXE = r"E:\game\幼なじみな彼女\osakano.exe"

# original Japanese (cp932)  ->  Chinese (cp936). Keep %s/%d and $RRGGBB codes verbatim.
TR = {
 "行動選択":"行动选择",
 "エンディング制覇":"通关结局",
 "ゲームクリア":"游戏通关",
 "好感度確認機能、エンディング一覧":"好感度查看、结局一览",
 "なし":"无",
 "ゲームを終了する  ( F7、Alt+Q )":"退出游戏  ( F7、Alt+Q )",
 "タイトルへ戻る  ( F6、Alt+T )":"返回标题  ( F6、Alt+T )",
 "環境設定  ( F3、Alt+C )":"环境设置  ( F3、Alt+C )",
 "ゲームを再開  ( F2、Alt+L )":"继续游戏  ( F2、Alt+L )",
 "ゲームを保存  ( F1、Alt+S )":"保存游戏  ( F1、Alt+S )",
 "ゲームを終了する":"退出游戏",
 "タイトルへ戻る":"返回标题",
 "ゲームに戻る":"返回游戏",
 "バックログ（巻き戻し）":"回看（倒回）",
 "既読スキップ":"已读跳过",
 "環境設定":"环境设置",
 "ゲームを再開":"继续游戏",
 "ゲームを保存":"保存游戏",
 "DirectXが存在しないか、バージョン条件を満たしていないので起動出来ません":"DirectX不存在或版本不满足，无法启动",
 "メッセージ":"消息",
 "閉じる":"关闭",
 "$0000FF×$FFFFFF いいえ":"$0000FF×$FFFFFF 否",
 "$FFFF00○$FFFFFF は　い":"$FFFF00○$FFFFFF 是",
 "Ｙ／Ｎ選択":"Ｙ／Ｎ选择",
 "現在の画面サイズ : %s":"当前画面尺寸 : %s",
 "ハイカラー（６万色）":"高彩（6万色）",
 "フルカラー（１６７７万色）":"全彩（1677万色）",
 "現在の画面はフルカラーモード":"当前画面为全彩模式",
 "フルカラーモードでの実行を推奨します。":"建议在全彩模式下运行。",
 "警告":"警告",
 "解像度の変更に失敗しました":"分辨率更改失败",
 "エラー":"错误",
 "起動不能（800x600以上の解像度が必要）":"无法启动（需800x600以上分辨率）",
 "起動可能（WINDOWモード）":"可启动（窗口模式）",
 "起動可能（フルスクリーンモード）":"可启动（全屏模式）",
 "ヒロインの名前":"女主名字",
 "大切な人の名前は？":"重要之人的名字？",
 "ロードに失敗しました":"读取失败",
 "セーブに失敗しました":"保存失败",
 "セーブが完了しました":"保存完成",
 "◆選択肢◆%s":"◆选项◆%s",
 "ロードするファイルがありません":"没有可读取的文件",
 "(空き領域)":"(空区域)",
 "%d章":"%d章",
 "序章":"序章",
 "ロード　（過去に保存したデータを読み出して再開します）":"读档　（读取以前的存档继续游戏）",
 "セーブ　（現在の状態を保存します）":"存档　（保存当前进度）",
 "現在のシナリオ":"当前剧情",
 "場所":"地点",
 "番号":"编号",
 "このデータは壊れています":"此存档已损坏",
 "この名前は使用出来ません。":"该名字无法使用。",
 "プレイ時間 ： %d時間 %d分 %d秒":"游玩时间 ： %d时 %d分 %d秒",
 "キャンセル":"取消",
 "決定":"确定",
 "ゲームを終了しますか？":"要退出游戏吗？",
 "プログラムを終了します。":"程序即将退出。",
 "ゲームを終了する場合は「中止」を押してください。":"要退出游戏请按「中止」。",
 "ディスプレイ設定の変更":"显示设置更改",
 "過去のメッセージを確認出来ます":"可查看过去的消息",
 "次のメッセージが既読であればスキップします":"若下一条消息已读则跳过",
 "ＣＤオーディオのエラー":"CD音频错误",
 "ＣＤドライブのエラー":"CD驱动器错误",
 "音楽ＣＤではない":"不是音乐CD",
 "使用不能文字を削除しました。":"已删除不可用字符。",
 "有効な文字が無くなりました。":"已没有有效字符。",
 "（半角文字は使用不可）":"（不可用半角字符）",
 "ロードします。":"开始读取。",
 "このままロードすると、現在の情報は失われます。":"读取将丢失当前信息。",
}

def main():
    data = bytearray(open(EXE, "rb").read())
    ok = skip = fail = 0
    for jp, zh in TR.items():
        try:
            jb = jp.encode("cp932")
        except Exception as e:
            print(f"[skip-enc] {jp!r}: {e}"); skip += 1; continue
        idx = data.find(jb)
        if idx < 0:
            print(f"[not-found] {jp!r}"); skip += 1; continue
        # require null terminator right after (so it's a real C string, not a substring)
        # find the actual run length (jb length, terminator follows)
        zb = zh.encode("cp936", "replace")
        if len(zb) > len(jb):
            print(f"[too-long] {jp!r} zh={len(zb)} > jp={len(jb)}"); fail += 1; continue
        # find a NULL-BOUNDED occurrence (complete C string, not a substring)
        start = 0; hit = -1
        while True:
            idx = data.find(jb, start)
            if idx < 0: break
            before_ok = (idx == 0 or data[idx-1] == 0)
            after_ok = (idx + len(jb) < len(data) and data[idx + len(jb)] == 0)
            if before_ok and after_ok:
                hit = idx; break
            start = idx + 1
        if hit < 0 and len(jb) >= 12:
            # fallback: long unique string -> require only NUL terminator after
            start = 0
            while True:
                idx = data.find(jb, start)
                if idx < 0: break
                if idx + len(jb) < len(data) and data[idx + len(jb)] == 0:
                    hit = idx; break
                start = idx + 1
        if hit < 0:
            print(f"[no-cstring] {jp!r}"); skip += 1; continue
        new = zb + b"\x00" * (len(jb) - len(zb))
        data[hit:hit+len(jb)] = new
        ok += 1
    open(EXE, "wb").write(data)
    print(f"\nUI strings patched: ok={ok} skip={skip} too_long={fail} (total map={len(TR)})")
    # sync to build/
    import shutil
    shutil.copy(EXE, r"E:\game\_work\build\osakano.exe")
    print("synced -> build\\osakano.exe")

main()
