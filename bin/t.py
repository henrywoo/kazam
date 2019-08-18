import configparser

#config = configparser.RawConfigParser()
config = configparser.ConfigParser({"x":1}, default_section='default')

# Please note that using RawConfigParser's set functions, you can assign
# non-string values to keys internally, but will receive an error when
# attempting to write to a file or when you get it in non-raw mode. Setting
# values using the mapping protocol or ConfigParser's set() does not allow
# such assignments to take place.
config.add_section('DEFAULT')
config.set('DEFAULT', 'an_int', '15')
config.set('DEFAULT', 'a_bool', 'true')
config.set('DEFAULT', 'a_float', '3.1415')
config.set('DEFAULT', 'baz', 'fun')
config.set('DEFAULT', 'bar', 'Python')
config.set('DEFAULT', 'foo', '%(bar)s is %(baz)s!')

# Writing our configuration file to 'example.cfg'
with open('example.cfg', 'w') as configfile:
    config.write(configfile)
