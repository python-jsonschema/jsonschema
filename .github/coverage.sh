set -e
printf '### Coverage\n\n' >>$GITHUB_STEP_SUMMARY
"$1" -m coverage report --format=markdown --show-missing >>$GITHUB_STEP_SUMMARY
