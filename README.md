# Indirect branches setter
_A plugin that eases setting undetermined indirect jump branches_

# Description
This plugin allows you to easily set the indirect jump branches targets for a given indirect jump. This is helpful in situations where binja fails to identify jump tables. To fix this, previously you would have to use the python console, but with this plugin you can do it from a simple UI.

You can insert the target addresses as a single addr (hex or decimal) (e.g. `0x2000` or `123`) or a comma separated list (e.g. `0x1d80, 0x1dc0, 0x1de0, 0x1df0, 0x1e00`) as shown in the gif. Better quality video [here](./images/out.mp4)

![usage gif](./images/out.gif)

# Install
To install this plugin, navigate to your Binary Ninja plugins directory, and run `git clone git@github.com:Vasco-jofra/indirect-branch-setter.git`.

# License
This plugin is released under a MIT license.