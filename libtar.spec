#
# Conditional build:
%bcond_without	tests	# regression tests

Summary:	C library for manipulating POSIX tar files
Summary(pl.UTF-8):	Biblioteka C do manipulacji plikami tar zgodnymi z POSIX
Name:		libtar
Version:	1.2.20
Release:	3
License:	BSD
Group:		Libraries
Source0:	https://deb.debian.org/debian/pool/main/libt/libtar/%{name}_%{version}.orig.tar.gz
# Source0-md5:	6ced95ab3a4b33fbfe2dfb231d156cdb
Source1:	%{name}-tests.py
Source2:	%{name}-test.c
Patch0:		%{name}-format.patch
Patch1:		%{name}-nostrip.patch
Patch2:		%{name}-CVE-2013-4420.patch
Patch3:		%{name}-CVE-2021-33643-33646.patch
Patch4:		%{name}-gzip.patch
URL:		https://repo.or.cz/w/libtar.git
BuildRequires:	autoconf >= 2.61
BuildRequires:	automake
BuildRequires:	libtool
%if %{with tests}
BuildRequires:	python3
%endif
BuildRequires:	zlib-devel
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
C library for manipulating POSIX tar files. It handles adding and
extracting files from a tar archive.

%description -l pl.UTF-8
Biblioteka C do manipulacji plikami tar zgodnymi z POSIX. Umożliwia
dodawanie oraz odzyskiwanie plików z archiwum tar.

%package devel
Summary:	Header files for libtar library
Summary(pl.UTF-8):	Pliki nagłówkowe biblioteki libtar
Group:		Development/Libraries
Requires:	%{name} = %{version}-%{release}

%description devel
Header files for libtar library.

%description devel -l pl.UTF-8
Pliki nagłówkowe biblioteki libtar.

%package static
Summary:	Static libtar library
Summary(pl.UTF-8):	Statyczna biblioteka libtar
Group:		Development/Libraries
Requires:	%{name}-devel = %{version}-%{release}

%description static
Static libtar library.

%description static -l pl.UTF-8
Statyczna biblioteka libtar.

%prep
%setup -q -n %{name}
%patch -P0 -p1
%patch -P1 -p1
%patch -P2 -p1
%patch -P3 -p1
%patch -P4 -p1

%build
%{__libtoolize}
%{__aclocal} -I autoconf
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	--with-zlib
%{__make}

%if %{with tests}
%{__cc} %{rpmcppflags} %{rpmcflags} -Ilib -Ilisthash \
	%{SOURCE2} -Llib/.libs -ltar %{rpmldflags} -o libtar-test
%{__python3} %{SOURCE1} libtar/.libs/libtar lib/.libs ./libtar-test
%endif

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%post	-p /sbin/ldconfig
%postun	-p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc COPYRIGHT ChangeLog ChangeLog-1.0.x README TODO
%attr(755,root,root) %{_bindir}/libtar
%attr(755,root,root) %{_libdir}/libtar.so.*.*.*
%ghost %{_libdir}/libtar.so.0

%files devel
%defattr(644,root,root,755)
%{_libdir}/libtar.so
%{_libdir}/libtar.la
%{_includedir}/libtar.h
%{_includedir}/libtar_listhash.h
%{_mandir}/man3/TH_*.3*
%{_mandir}/man3/libtar_*.3*
%{_mandir}/man3/tar_*.3*
%{_mandir}/man3/th_*.3*

%files static
%defattr(644,root,root,755)
%{_libdir}/libtar.a
