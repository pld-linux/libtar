Summary:	C library for manipulating POSIX tar files
Summary(pl.UTF-8):	Biblioteka C do manipulacji plikami tar zgodnymi z POSIX
Name:		libtar
Version:	1.2.11
Release:	2
License:	BSD
Group:		Libraries
Source0:	ftp://ftp.feep.net/pub/software/libtar/%{name}-%{version}.tar.gz
# Source0-md5:	604238e8734ce6e25347a58c4f1a1d7e
Patch0:		%{name}-shared.patch
Patch1:		%{name}-fix-memleak.patch
URL:		http://www.feep.net/libtar/
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libtool
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
%setup -q
%patch0 -p1
%patch1 -p1

%build
# ugly, but working solution
cat %{_aclocaldir}/libtool.m4 >> autoconf/aclocal.m4
cat %{_aclocaldir}/ltoptions.m4 >> autoconf/aclocal.m4
cat %{_aclocaldir}/ltversion.m4 >> autoconf/aclocal.m4
cat %{_aclocaldir}/ltsugar.m4 >> autoconf/aclocal.m4
cp %{_datadir}/libtool/build-aux/config.{sub,guess} autoconf
%{__libtoolize}
%{__autoconf} -I autoconf
%configure
%{__make}

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
%attr(755,root,root) %ghost %{_libdir}/libtar.so.0

%files devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/libtar.so
%{_libdir}/libtar.la
%{_includedir}/*.h
%{_mandir}/man3/*.3*

%files static
%defattr(644,root,root,755)
%{_libdir}/libtar.a
