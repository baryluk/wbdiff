#!/bin/sh

for t in tests/*
do
	echo "Checking $t"
	./wbdiff.py "$t/left" "$t/right" > "$t/output"
	cmp "$t/output" "$t/expected"
	O=$?
	diff "$t/output" "$t/expected"
	if [ "x$O" = "x0" ]; then
		echo "OK"
	else
		echo "FAIL"
		exit $O
	fi
done
