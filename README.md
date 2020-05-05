# sudobless

Grant a terminal a sudo session

## Example

User ensures sudo timestamp file exists:
```
user@host:~$ sudo -i
[sudo] password for user: ^C
user@host:~$ echo $$
96683
user@host:~$ 
```

Root blesses user:
```
root@host:~# sudobless 96683
root@host:~# 
```

User can now sudo without a password prompt:
```
user@host:~$ sudo -i
root@host:~# 
```

## Install

Python 3 required

```
install -T -m744 -o root -g root sudobless.py /usr/local/bin/sudobless
```

## Notes

* Use at your own risk. If you mess something up, run `sudo -K` as the user you blessed to wipe all the sudo sessions.
* This is tested on Arch Linux (kernel 5.5) x86_64 with sudo >= 1.8.22. It might not run on non-Linux
