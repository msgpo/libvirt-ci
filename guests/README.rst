===================================
libvirt CI - guest management tools
===================================

The tools contained in this directory simplify and automate the management
of the container and VM images used by the libvirt CI infrastructure.


Usage and examples
==================

There are two steps to bringing up a guest:

* ``lcitool install $guest`` will perform an unattended installation
  of ``$guest``. Not all guests can be installed this way: see the "FreeBSD"
  section below;

* ``lcitool update $guest $project`` will go through all the
  post-installation configuration steps required to make the newly-created
  guest usable and ready to be used for building ``$project``;

Once those steps have been performed, maintenance will involve running:

::

   $ lcitool update $guest $project

periodically to ensure the guest configuration is sane and all installed
packages are updated.

To get a list of known guests and projects, run

::

   $ lcitool hosts

and

::

   $ lcitool projects

respectively. You can run operations involving multiple guests and projects
at once by providing a list on the command line: for example, running

::

   $ lcitool update '*fedora*' '*osinfo*'

will update all Fedora guests and get them ready to build libosinfo and
related projects, while running

::

   $ lcitool update all 'libvirt,libvirt+mingw*'

will update all hosts and prepare them to build libvirt both as a native
library and, where supported, as a Windows library using MinGW.

Once hosts have been prepared following the steps above, you can use
``lcitool`` to perform builds as well: for example, running

::

   $ lcitool build '*debian*' libvirt-python

will fetch libvirt-python's ``master`` branch from the upstream repository
and build it on all Debian hosts.

You can add more git repositories by tweaking the ``git_urls`` dictionary
defined in ``playbooks/build/jobs/defaults.yml`` and then build arbitrary
branches out of those with

::

   $ lcitool build -g github/cool-feature all libvirt


Host setup
==========

``ansible`` and ``virt-install`` need to be available on the host, the former
can be either installed system-wide using your package manager or using ``pip``
(see the provided ``requirements.txt`` file). The latter can only be installed
with your package manager as ``virt-install`` is not distributed via PyPI.

Before you can start bringing up guests, you need to create
``~/.config/lcitool/config.yaml``, ideally by copying the ``config.yaml``
template, and set at least the options marked as "(mandatory)" depending on
the flavor (``test``, ``gitlab``) you wish to use with your
machines.

Ansible expects to be able to connect to the guests by name: installing and
enabling the `libvirt NSS plugin <https://wiki.libvirt.org/page/NSS_module>`_
on the host is the easiest way to make sure that works. More specifically,
you'll want to use the ``libvirt_guest`` variant of the plugin.

To keep guests up to date over time, it's recommended to have an entry
along the lines of

::

   0 0 * * * ~/libvirt-ci/guests/lcitool update all all

in your crontab.


Test use
========

If you are a developer trying to reproduce a bug on some OS you don't
have easy access to, you can use these tools to create a suitable test
environment.

The ``test`` flavor is used by default, so you don't need to do anything
special in order to use it: just follow the steps outlined above. Once
a guest has been prepared, you'll be able to log in as ``test`` either
via SSH (your public key will have been authorized) or on the serial
console (password: ``test``).

Once logged in, you'll be able to perform administrative tasks using
``sudo``. Regular root access will still be available, either through
SSH or on the serial console.

Since guests created for this purpose are probably not going to be
long-lived or contain valuable information, you can configure your
SSH client to skip some of the usual verification steps and thus
prompt you less frequently; moreover, you can have the username
selected automatically for you to avoid having to type it in every
single time you want to connect. Just add

::

   Host libvirt-*
       User test
       GSSAPIAuthentication no
       StrictHostKeyChecking no
       CheckHostIP no
       UserKnownHostsFile /dev/null

to your ``~/.ssh/config`` file to achieve all of the above.


Cloud-init
==========

If you intend to use the generated images as templates to be instantiated in
a cloud environment like OpenStack, then you want to set the
``install.cloud_init`` key to ``true`` in ``~/.config/lcitool/config.yaml``. This will
install the necessary cloud-init packages and enable the corresponding services
at boot time. However, there are still a few manual steps involved to create a
generic template. You'll need to install the ``libguestfs-tools`` package for that.

Once you have it installed, shutdown the machines gracefully. First, we're going to
"unconfigure" the machine in a way, so that clones can be made out of it.

::

    $ virt-sysprep -a libvirt-<machine_distro>.qcow2

Then, we sparsify and compress the image in order to shrink the disk to the
smallest size possible

::

    $ virt-sparsify --compress --format qcow2 <indisk> <outdisk>

Now you're ready to upload the image to your cloud provider, e.g. OpenStack

::

    $ glance image-create --name <image_name> --disk-format qcow2 --file <outdisk>

FreeBSD is tricky with regards to cloud-init, so have a look at the
`Cloud-init with FreeBSD`_ section instead.


FreeBSD
=======

Installation of FreeBSD guests must be performed manually; alternatively,
the official qcow2 images can be used to quickly bring up such guests.

::

   $ MAJOR=12
   $ MINOR=1
   $ VER=$MAJOR.$MINOR-RELEASE
   $ sudo wget -O /var/lib/libvirt/images/libvirt-freebsd-$MAJOR.qcow2.xz \
     https://download.freebsd.org/ftp/releases/VM-IMAGES/$VER/amd64/Latest/FreeBSD-$VER-amd64.qcow2.xz
   $ sudo unxz /var/lib/libvirt/images/libvirt-freebsd-$MAJOR.qcow2.xz
   $ virt-install \
     --import \
     --name libvirt-freebsd-$MAJOR \
     --vcpus 2 \
     --graphics vnc \
     --noautoconsole \
     --console pty \
     --sound none \
     --rng device=/dev/urandom,model=virtio \
     --memory 2048 \
     --os-variant freebsd$MAJOR.0 \
     --disk /var/lib/libvirt/images/libvirt-freebsd-$MAJOR.qcow2

The default qcow2 images are sized too small to be usable. To enlarge
them do

::

   $ virsh blockresize libvirt-freebsd-$MAJOR \
     /var/lib/libvirt/images/libvirt-freebsd-$MAJOR.qcow2 15G

Then inside the guest, as root, enlarge the 3rd partition & filesystem
to consume all new space:

::

   # gpart resize -i 3 vtbd0
   # service growfs onestart

Some manual tweaking will be needed, in particular:

* ``/etc/ssh/sshd_config`` must contain the ``PermitRootLogin yes`` directive;

* ``/etc/rc.conf`` must contain the ``sshd_enable="YES"`` setting;

* the root password must be manually set to "root" (without quotes).

Once these steps have been performed, FreeBSD guests can be managed just
like all other guests.

Cloud-init with FreeBSD
-----------------------

FreeBSD doesn't fully support cloud-init, so in order to make use of it, there
are a bunch of manual steps involved. First, you want to install the base OS
manually rather than use the official qcow2 images, in contrast to the
suggestion above, because cloud-init requires a specific disk partitioning scheme.
Best you can do is to look at the official
`OpenStack guide <https://docs.openstack.org/image-guide/freebsd-image.html>`_
and follow only the installation guide (along with the ``virt-install`` steps
outlined above).

Now, that you have and OS installed and booted, set the ``install.cloud_init``
key to ``true`` in ``~/.config/lcitool/config.yaml`` and update it with the
desired project.

The sysprep phase is completely manual, as ``virt-sysprep`` cannot work with
FreeBSD's UFS filesystem (because the Linux kernel can only mount it read-only).

Compressing and uploading the image looks the same as was mentioned in the
earlier sections

::

    $ virt-sparsify --compress --format qcow2 <indisk> <outdisk>
    $ glance image-create --name <image_name> --disk-format qcow2 --file <outdisk>


Adding new guests
=================

Adding new guests will require tweaking the inventory and host variables,
but it should be very easy to eg. use the Fedora 26 configuration to come
up with a working Fedora 27 configuration.
