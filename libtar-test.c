/* Read one header and close, including incomplete GNU extension error paths. */
#include <libtar.h>
#include <fcntl.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
	TAR *t;
	int status;
	if (argc != 3 || tar_open(&t, argv[1], NULL, O_RDONLY, 0, 0) != 0)
		return 2;
	status = th_read(t);
	if (tar_close(t) != 0)
		return 3;
	return status != atoi(argv[2]);
}
