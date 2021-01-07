#!/bin/bash

#set -e
#set -x

# Diff for showing failed tests (differing actual output vs expected output).
DIFF=("diff" "-Nu")
if which colordiff >/dev/null; then
  DIFF=("colordiff" "-Nu")
fi
if which wdiff >/dev/null; then
  DIFF=("wdiff" $(echo -e "--start-delete=\e[91m") $(echo -e "--end-delete=\e[0m") $(echo -e "--start-insert=\e[92m") $(echo -e "--end-insert=\e[0m"))
fi

# Dogfooding is also possible.
if which wbdiff >/dev/null; then
  DIFF=("wbdiff" "--skip-equal" "--fuzzy" "--no-header")
fi

for t in tests/*
do
	echo "Checking $t"
	if ! [ -f "$t/expected" ]; then
		echo "MISSING_EXPECTED_FILE"
		continue
	fi
	if ! [ -f "$t/left" ] && ! [ -f "$t/right" ]; then
		echo "MISSING_INPUT_FILES"
		continue
	fi
	FUZZY=()
	if echo "$t" | grep -q "fuzzy"; then
		FUZZY=("--fuzzy" "--fuzzy-weighted")
	fi
	# Uncomment if you want to update expected output files.
	# BE ABSOLUTLY SURE THEY ARE CORRECT!
	#./wbdiff "${FUZZY[@]}" --no-color -- "$t/left" "$t/right" > "$t/expected"
	env time ./wbdiff "${FUZZY[@]}" --no-color -- "$t/left" "$t/right" > "$t/output"
	grep -v 'Initial context length used' "$t/expected" > "$t/expected.filtered"
	grep -v 'Initial context length used' "$t/output" > "$t/output.filtered"
	cmp "$t/expected.filtered" "$t/output.filtered"
	O=$?
	"${DIFF[@]}" "$t/expected.filtered" "$t/output.filtered"
	if [ "x$O" = "x0" ]; then
		echo "OK"
	else
		echo "FAIL"
		exit $O
	fi
	echo
done
