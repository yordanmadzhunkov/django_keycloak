# Install Pyenv on Ubuntu 22.04
Get the Required Dependencies

```
sudo apt-get update; sudo apt-get install make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

# Install Pyenv

https://github.com/pyenv/pyenv-installer

`curl https://pyenv.run | bash`

Make sure this is in your .bashrc

```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

`pyenv install 3.10.11`



