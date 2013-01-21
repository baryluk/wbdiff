#!/bin/sh

for t in tests/*
do
	echo "Checking $t"
	if ! [ -f "$t/expected" ]; then
		echo "SKIPPED"
		continue
	fi
	# Uncomment if you want to update expected output files.
	# BE ABSOLUTLY SURE THEY ARE CORRECT!
	#./wbdiff.py --no-color "$t/left" "$t/right" > "$t/expected"
	./wbdiff.py --no-color "$t/left" "$t/right" > "$t/output"
	grep -v 'Initial context length used' "$t/expected" > "$t/expected.filtered"
	grep -v 'Initial context length used' "$t/output" > "$t/output.filtered"
	cmp "$t/output.filtered" "$t/expected.filtered"
	O=$?
	diff "$t/output.filtered" "$t/expected.filtered"
	if [ "x$O" = "x0" ]; then
		echo "OK"
	else
		echo "FAIL"
		exit $O
	fi
done
