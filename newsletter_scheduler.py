"""Weekly newsletter scheduler.

Usage example:
  export SMTP_HOST=smtp.gmail.com
  export SMTP_PORT=587
  export SMTP_USER=your_email@gmail.com
  export SMTP_PASSWORD=your_app_password
  export NEWSLETTER_FROM=your_email@gmail.com
  export NEWSLETTER_TO=alice@example.com,bob@example.com

  python newsletter_scheduler.py \
    --weekday mon \
    --time 09:30 \
    --subject "주간 뉴스레터" \
    --body-file ./newsletter_body.txt

This script runs continuously and sends one email per scheduled week.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

WEEKDAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


@dataclass
class MailConfig:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    sender: str
    recipients: list[str]


@dataclass
class ScheduleConfig:
    weekday: int
    hour: int
    minute: int
    timezone: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="매주 지정 시간 뉴스레터 발송 스케줄러")
    parser.add_argument("--weekday", default="mon", choices=WEEKDAY_MAP.keys(), help="발송 요일")
    parser.add_argument("--time", default="09:00", help="발송 시간(HH:MM, 24시간 형식)")
    parser.add_argument("--timezone", default="Asia/Seoul", help="타임존 (예: Asia/Seoul)")
    parser.add_argument("--subject", default="주간 뉴스레터", help="메일 제목")
    parser.add_argument("--body", default="안녕하세요. 주간 뉴스레터입니다.", help="메일 본문")
    parser.add_argument("--body-file", help="메일 본문 파일 경로(.txt)")
    parser.add_argument("--poll-seconds", type=int, default=20, help="스케줄 체크 주기(초)")
    return parser.parse_args()


def get_mail_config() -> MailConfig:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("NEWSLETTER_FROM", smtp_user)
    recipients_raw = os.getenv("NEWSLETTER_TO", "")

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    if not smtp_host or not smtp_user or not smtp_password or not sender or not recipients:
        raise ValueError(
            "환경변수 누락: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NEWSLETTER_FROM(선택), NEWSLETTER_TO(쉼표 구분)"
        )

    return MailConfig(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        sender=sender,
        recipients=recipients,
    )


def parse_schedule_config(args: argparse.Namespace) -> ScheduleConfig:
    try:
        hour_str, minute_str = args.time.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
    except ValueError as exc:
        raise ValueError("--time 형식이 잘못되었습니다. 예: 09:30") from exc

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("--time 값 범위가 잘못되었습니다. HH(0~23):MM(0~59)")

    return ScheduleConfig(
        weekday=WEEKDAY_MAP[args.weekday],
        hour=hour,
        minute=minute,
        timezone=args.timezone,
    )


def load_body(args: argparse.Namespace) -> str:
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as file:
            return file.read()
    return args.body


def next_run_at(now: datetime, schedule: ScheduleConfig) -> datetime:
    days_ahead = (schedule.weekday - now.weekday()) % 7
    candidate = now.replace(hour=schedule.hour, minute=schedule.minute, second=0, microsecond=0)
    if days_ahead == 0 and candidate <= now:
        days_ahead = 7
    return candidate + timedelta(days=days_ahead)


def send_newsletter(mail: MailConfig, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = mail.sender
    message["To"] = ", ".join(mail.recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(mail.smtp_host, mail.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(mail.smtp_user, mail.smtp_password)
        smtp.send_message(message)


def run_scheduler(mail: MailConfig, schedule: ScheduleConfig, subject: str, body: str, poll_seconds: int) -> None:
    tz = ZoneInfo(schedule.timezone)
    print(f"[시작] 매주 {schedule.weekday}요일 {schedule.hour:02d}:{schedule.minute:02d} ({schedule.timezone}) 발송")

    next_run = next_run_at(datetime.now(tz), schedule)
    print(f"[대기] 다음 발송 예정 시각: {next_run.isoformat()}")

    while True:
        now = datetime.now(tz)
        if now >= next_run:
            try:
                send_newsletter(mail, subject, body)
                print(f"[성공] 뉴스레터 발송 완료: {now.isoformat()}")
            except Exception as exc:  # noqa: BLE001
                print(f"[오류] 뉴스레터 발송 실패: {exc}")

            next_run = next_run + timedelta(days=7)
            print(f"[대기] 다음 발송 예정 시각: {next_run.isoformat()}")

        time.sleep(poll_seconds)


def main() -> None:
    args = parse_args()
    mail = get_mail_config()
    schedule = parse_schedule_config(args)
    body = load_body(args)
    run_scheduler(mail, schedule, args.subject, body, args.poll_seconds)


if __name__ == "__main__":
    main()
