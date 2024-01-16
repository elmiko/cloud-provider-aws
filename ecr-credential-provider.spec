# Built from this template:
# https://github.com/openshift/release/blob/master/tools/hack/golang/package.spec
#
# See also: https://github.com/openshift/kubernetes/blob/master/openshift.spec

#debuginfo not supported with Go
%global debug_package %{nil}

# modifying the Go binaries breaks the DWARF debugging
%global __os_install_post %{_rpmconfigdir}/brp-compress

# %commit and %os_git_vars are intended to be set by tito custom builders
# provided in the .tito/lib directory. The values in this spec file will not be
# kept up to date.
%{!?commit: %global commit HEAD }
%global shortcommit %(c=%{commit}; echo ${c:0:7})
# os_git_vars needed to run hack scripts during rpm builds
%{!?os_git_vars: %global os_git_vars OS_GIT_VERSION='' OS_GIT_COMMIT='' OS_GIT_MAJOR='' OS_GIT_MINOR='' OS_GIT_TREE_STATE='' }

%if 0%{?skip_build}
%global do_build 0
%else
%global do_build 1
%endif
%if 0%{?skip_prep}
%global do_prep 0
%else
%global do_prep 1
%endif

%if 0%{?fedora} || 0%{?epel}
%global need_redistributable_set 0
%else
# Due to library availability, redistributable builds only work on x86_64
%ifarch x86_64
%global need_redistributable_set 1
%else
%global need_redistributable_set 0
%endif
%endif
%{!?make_redistributable: %global make_redistributable %{need_redistributable_set}}

#
# Customize from here.
#

%global golang_version 1.21.0
%{!?version: %global version 0.0.1}
%{!?release: %global release 1}
%global package_name ecr-credential-provider 
%global product_name ecr-credential-provider

Name:           %{package_name}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        AWS ecr kubelet image credential provider
License:        ASL 2.0

Source0:        %{name}-%{version}.tar.gz
BuildRequires:  bsdtar
BuildRequires:  golang >= %{golang_version}

# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:  x86_64 aarch64 ppc64le s390x
%endif

### AUTO-BUNDLED-GEN-ENTRY-POINT

%description
This package provides the ecr-credential-provider. It is a kubelet image
credential provider. It dynamically provides kubelet with credentials to pull
images from ecr. For more information see:
https://kubernetes.io/docs/tasks/administer-cluster/kubelet-credential-provider/

%prep
%if 0%{do_prep}
%setup -q
%endif

%build

%if 0%{do_build}
# Expand os_git_vars macro so we can use the variables it defines
%{os_git_vars}

# This is likely unneeded, however we are leaving it in to stick as closeley to
# the template as possible in case anything changes in the future.
#
# We call the same make target as below. See the comment below for more detail
%if 0%{make_redistributable}
# Create Binaries for all internally defined arches
VERSION=v${OS_GIT_VERSION} make ecr-credential-provider 
%else
# Create Binaries only for building arch
%ifarch x86_64
  BUILD_PLATFORM="linux/amd64"
%endif
%ifarch %{ix86}
  BUILD_PLATFORM="linux/386"
%endif
%ifarch ppc64le
  BUILD_PLATFORM="linux/ppc64le"
%endif
%ifarch %{arm} aarch64
  BUILD_PLATFORM="linux/arm64"
%endif
%ifarch s390x
  BUILD_PLATFORM="linux/s390x"
%endif

# The upstream Makefile does not support providing BUILD_PLATFORM. We could
# include our own make definitions, but for now it is easier to rely on the
# behaviour of Brew.
#
# Brew (the build tooling for RPMs) will build on a machine where the desired
# arch matches the host arch. This means we can use the standard make target,
# as it builds for the arch that it detects.
VERSION=v${OS_GIT_VERSION} make ecr-credential-provider
%endif
%endif

%install

PLATFORM="$(go env GOHOSTOS)-$(go env GOHOSTARCH)"
install -d %{buildroot}%{_libexecdir}/kubelet-image-credential-provider-plugins

# Install linux components
for bin in ecr-credential-provider 
do
  echo "+++ INSTALLING ${bin}"
  install -p -m 755 %{_builddir}/%{name}-%{version}/${bin} %{buildroot}%{_libexecdir}/kubelet-image-credential-provider-plugins/${bin}
done

%files
%license LICENSE
%{_libexecdir}/kubelet-image-credential-provider-plugins/ecr-credential-provider

%pre

%changelog
* Thu Jan  11 2024 Theo Barber-Bany <tbarberb@redhat.com> - 0.0.1
- First version being packaged
