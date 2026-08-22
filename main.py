import json
import logging
import sys
from requests.exceptions import RequestException
import requests

# ログ出力の設定（エラーや処理の進捗を標準出力・標準エラーに分かりやすく記録する）
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 取得対象のURL（気象庁の公開天気予報JSON：東京都＝130000）
TARGET_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json"
OUTPUT_FILENAME = "data.json"


def fetch_weather_data(url):
  """指定されたURLから気象庁の天気予報JSONデータを安全に取得する。"""
  try:
    # タイムアウトを設定（無応答によるプログラムのフリーズを防ぐ）
    response = requests.get(url, timeout=10)

    # ステータスコードが4xxや5xxの場合に例外を発生させる
    response.raise_for_status()

    # レスポンスをJSONとしてパース
    return response.json()

  except requests.exceptions.HTTPError as http_err:
    logging.error(f"HTTPエラーが発生しました: {http_err} (URL: {url})")
  except requests.exceptions.ConnectionError as conn_err:
    logging.error(f"ネットワーク接続エラーが発生しました: {conn_err}")
  except requests.exceptions.Timeout as timeout_err:
    logging.error(f"リクエストがタイムアウトしました: {timeout_err}")
  except requests.exceptions.RequestException as req_err:
    logging.error(f"予期せぬリクエストエラーが発生しました: {req_err}")
  except ValueError as json_err:
    logging.error(f"JSONのパースに失敗しました: {json_err}")

  # 異常終了時は安全に終了コード1を返してクラッシュを防ぐ
  sys.exit(1)


def parse_weather_forecast(raw_data):
  """生データから必要な情報（地域名、日付、天気など）を抽出・整形する。"""
  try:
    parsed_results = []

    # 気象庁APIの構造（時系列・エリア別の階層）をパース
    # 最初の要素：時系列予報エリアごとのデータ
    time_series_data = raw_data[0]["timeSeries"]

    # 地域情報の取得（publishingOfficeやarea定義）
    areas = time_series_data[0]["areas"]

    for area in areas:
      area_name = area["area"]["name"]
      area_code = area["area"]["code"]
      time_defines = time_series_data[0]["timeDefines"]
      weathers = area["weathers"]

      # 日付と天気を紐付けてリスト化
      daily_forecasts = []
      for date_str, weather_desc in zip(time_defines, weathers):
        daily_forecasts.append({"date": date_str, "weather": weather_desc})

      parsed_results.append({
          "area_name": area_name,
          "area_code": area_code,
          "forecasts": daily_forecasts,
      })

    return parsed_results

  except (KeyError, IndexError) as e:
    logging.error(
        f"データ構造が期待される形式と異なります（API仕様変更の可能性）: {e}"
    )
    sys.exit(1)


def save_to_json(data, filename):
  """整形したデータを指定されたファイル名でローカルに保存する。"""
  try:
    with open(filename, "w", encoding="utf-8") as f:
      # 日本語の文字化けを防ぐため ensure_ascii=False を指定
      json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"データを正常に保存しました: {filename}")
  except IOError as io_err:
    logging.error(f"ファイルの書き込みに失敗しました: {io_err}")
    sys.exit(1)


def main():
  """メイン処理の実行フロー。"""
  logging.info("データ取得プロセスを開始します。")

  # 1. HTTPリクエストによるデータ取得
  raw_data = fetch_weather_data(TARGET_URL)

  # 2. データの抽出・構造化
  structured_data = parse_weather_forecast(raw_data)

  # 3. JSONファイルへの書き出し
  save_to_json(structured_data, OUTPUT_FILENAME)

  logging.info("すべての処理が正常に完了しました。")


if __name__ == "__main__":
  main()
