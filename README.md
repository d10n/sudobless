# sudobless

Let root grant a passwordless sudo session to a non-root shell. The user of the target shell must be in sudoers.

## Usage
```
sudobless <pid of shell>
```

## Example

<table><thead><tr><td>User terminal</td><td>Root terminal</td></tr></thead><tbody><tr><td rowspan="2">

User fails to sudo and checks the shell pid:
```
user@host:~$ sudo -i
[sudo] password for user: ^C
user@host:~$ echo $$
96683
user@host:~$ 
```
<td rowspan="2"></td></tr><tr></tr><tr><td rowspan="2"></td><td rowspan="2">

Root blesses user with the shell pid:
```
root@host:~# sudobless 96683
root@host:~# 
```
</td></tr><tr></tr><tr><td>

User can now sudo without a password prompt:
```
user@host:~$ sudo -i
root@host:~# 
```
</td><td></td></tr></tbody></table>

## Install

Python 3 required

```
install -T -m744 -o root -g root sudobless.py /usr/local/bin/sudobless
```

## Notes

* Use at your own risk. If you mess something up, run `sudo -K` as the user you blessed to wipe all the sudo sessions.
* This is tested on Arch Linux (kernel 5.5) x86_64 with sudo >= 1.8.22. It might not run on non-Linux
* The python is draft quality but it should be easy to read / audit
