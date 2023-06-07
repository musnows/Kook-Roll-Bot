.PHONY:ps
ps:
	ps jax | head -1 && ps jax | grep rollbot.py |  grep -v grep

.PHONY:run
run:
	nohup python3.10 -u rollbot.py >> /dev/null 2>&1 &