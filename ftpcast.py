import subprocess
import ftplib
import re
import signal
import sys
import os
import shutil
import tkinter as tk
from tkinter import ttk
import threading
import time

mount_point = "test_broadcast"#マウントポイントを指定します。この場合https://example.com/test_broadcast以下にファイルが送信される
server = 'example.com'#ftpサーバーのドメイン
user = 'yourusername'#ftpユーザー名
password = 'youruserpassword'#ftpパスワード
ftp = ftplib.FTP(server)
ftp.login(user, password)
# ディレクトリが存在しない場合は作成する
if mount_point not in ftp.nlst():
	ftp.mkd(mount_point)
ftp.cwd(mount_point)


def add_title_metadata(ts_file):
	# nowplaying.txtからタイトルを読み取る
	with open('nowplaying.txt', 'r') as file:
		title = file.read().strip()
	shutil.move(ts_file, ts_file + '_tmp.ts')
	# ffmpegコマンドの作成
	ffmpeg_cmd = [
		'ffmpeg',
		'-i', ts_file + '_tmp.ts',  # 入力ファイル名
		'-metadata', f'title={title}',  # タイトルメタデータの設定
		'-c', 'copy',  # ストリームをコピーして再エンコードしない
		f'{ts_file}'  # 出力ファイル名
	]

	# ffmpegを実行
	subprocess.run(ffmpeg_cmd)


def get_audio_devices():
	command = 'ffmpeg -list_devices true -f dshow -i dummy -hide_banner'
	try:
		output = subprocess.check_output(command, shell=True, encoding='utf-8', stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		output = e.output

	devices = []
	lines = output.split('\n')
	pattern = re.compile(r'\[dshow @ .+\] "(.*)" \(audio\)')

	for line in lines:
		match = pattern.search(line)
		if match:
			device_name = match.group(1)
			devices.append(device_name)

	return devices

def upload_file(file_path, mount_point):
	file_name = os.path.basename(file_path)
	with open(file_path, 'rb') as file:
		ftp.storbinary(f'STOR {file_name}', file)


def process_output(line, mount_point):
	if "[hls @" in line:
		file_name = line.strip()
		file_name = re.sub(r".*Opening '(.*?)' for writing.*", r"\1", file_name)
		file_name = re.sub(".m3u8.tmp", ".m3u8", file_name)
		while True:
			try:
				upload_file(file_name, mount_point)
				print("アップロード成功:" + file_name)
				break
			except:
				print("アップロード失敗:" + file_name)


def read_output(process, mount_point):
	for line in iter(process.stdout.readline, ''):
		process_output(line, mount_point)


def monitor_ffmpeg_output(command):
	process = subprocess.Popen(
		command,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		universal_newlines=True,
		bufsize=1,  # Adjust the buffer size as per your requirement
		errors="ignore"
	)
	print("配信開始")
	try:
		# Start a separate thread to read and process the output
		output_thread = threading.Thread(target=read_output, args=(process, mount_point))
		output_thread.start()

		# Wait for the output thread to finish while monitoring for KeyboardInterrupt
		while output_thread.is_alive():
			try:
				output_thread.join(timeout=1)
			except KeyboardInterrupt:
				print("Ctrl+Cが押されました。ffmpegプロセスを終了します。")
				process.terminate()
				process.wait()
				sys.exit(0)

	finally:
		process.stdout.close()
		process.wait()


def start_stream():
	bitrate = bitrate_var.get()
	codec = "aac"
	if codec == "opus":
		ffmpeg_command = [
			"ffmpeg_vvceasy.exe",
			"-f",
			"dshow",
			"-i",
			"audio=" + audio_device_var.get(),
			"-c:v",
			"copy",
			"-c:a",
			"libopus",
			"-b:a",
			bitrate + "k",
			"-ar",
			"44100",
			"-strict",
			"-2",
			"./segment/output.m3u8"
		]
	elif codec == "aac":
		ffmpeg_command = [
			"ffmpeg_vvceasy.exe",
			"-f",
			"dshow",
			"-i",
			"audio=" + audio_device_var.get(),
			"-c:v",
			"copy",
			"-c:a",
			"libfdk_aac",
			"-profile:a",
			"aac_he_v2",
			"-b:a",
			bitrate + "k",
			"-ar",
			"44100",
			"-strict",
			"-2",
			"./segment/output.m3u8"
		]


	segment_dir = './segment/'
	if os.path.exists(segment_dir):
		shutil.rmtree(segment_dir)
	os.makedirs(segment_dir)

	monitor_ffmpeg_output(ffmpeg_command)


def restart_program():
	python = sys.executable
	os.execl(python, python, *sys.argv)


def stop_stream():
	restart_program()
	os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)


def on_start_button_click():
	start_thread = threading.Thread(target=start_stream)
	start_thread.start()
	start_button.config(state=tk.DISABLED)
	stop_button.config(state=tk.NORMAL)


def on_stop_button_click():
	stop_stream()
	start_button.config(state=tk.NORMAL)
	stop_button.config(state=tk.DISABLED)


def upload_file_thread(file_path, mount_point):
	upload_thread = threading.Thread(target=upload_file, args=(file_path, mount_point))
	upload_thread.start()


root = tk.Tk()
root.title("ストリーミング配信")

bitrate_label = ttk.Label(root, text="ビットレート:")
bitrate_label.pack()
bitrate_var = tk.StringVar()
bitrate_combobox = ttk.Combobox(root, textvariable=bitrate_var,
								values=["8", "12", "16", "24", "32", "48", "56", "64", "96", "128", "192"])
bitrate_combobox.set("64")
bitrate_combobox.pack()

audio_device_label = ttk.Label(root, text="オーディオデバイス:")
audio_device_label.pack()
audio_device_var = tk.StringVar()
audio_device_combobox = ttk.Combobox(root, textvariable=audio_device_var, values=get_audio_devices())
audio_device_combobox.set(get_audio_devices()[0])
audio_device_combobox.pack()

start_button = ttk.Button(root, text="配信開始", command=on_start_button_click)
start_button.pack()

stop_button = ttk.Button(root, text="配信停止", command=on_stop_button_click, state=tk.DISABLED)
stop_button.pack()

root.mainloop()
