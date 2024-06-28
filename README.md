# ftpcast
FTPを介して音声をストリーミング配信する実証実験用コードです。実験目的のため不安定です。
## 使い方
1. ftpcast.py内の必須項目を設定する
```python
mount_point = "test_broadcast"#マウントポイントを指定します。この場合https://example.com/test_broadcast以下にファイルが送信される
server = 'example.com'#ftpサーバーのドメイン
user = 'yourusername'#ftpユーザー名
password = 'youruserpassword'#ftpパスワード
```
2. ftpcast.pyを実行する。
3. {server}/{mount_point}/segment/output.m3u8にVLCなど対応プレイヤーからアクセスする。
