mod-ip-tag
==========

Shinken module for tagging hosts based on their IP range. The module definition looks as:

```
define module{
       module_name	DMZ_Zone
       module_type	ip-tag
       ip_range         172.10.0.0/24
       method           replace
       property         poller_tag
       value            DMZ
}

```


Properties
==========

__module_name__ 

Set what yoy want here, must be unique

__module_type__

Should be ip-tag

__ip_range__

The IP Range where the tag will apply. Will look at the host address name resolution or it's ip if it's already an IP


