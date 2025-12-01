#!/usr/bin/env bash
# refactor → main 덮어씌우기 자동화 스크립트

set -e  # 에러 발생 시 즉시 중단

# 현재 refactor 브랜치에서 최신 코드 커밋 & 푸시
echo "Committing and pushing changes on refactor..."
git add .
git commit -m "$(date '+%Y-%m-%d %H:%M:%S')"
git push -u origin refactor

# main 브랜치로 이동
echo "Switching to main..."
git checkout main

# main을 refactor 상태로 강제 맞춤
echo "Resetting main to match refactor..."
git fetch origin
git reset --hard refactor

# 원격 main도 강제 업데이트
echo "Force pushing main to origin..."
git push origin main --force-with-lease

# 다시 refactor 브랜치로 복귀
echo "Switching back to refactor..."
git checkout refactor

echo "Done! main is now identical to refactor."
