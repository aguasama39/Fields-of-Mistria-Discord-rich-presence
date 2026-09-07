#include <adwaita.h>

int main(void)
{
    return adw_get_major_version() > 0 ? 0 : 1;
}
