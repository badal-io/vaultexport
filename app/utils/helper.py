import toml
from constants import export_format

def merge_dict(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def write_env_config(filename, data, file_format):
    # log.info("writing secrets to " + filename)
    # Generates the secrets in key=value or toml
    fh = open(filename, "w")
    if file_format == export_format.TOML:
        fh.write(toml.dumps(data))
    else:
        for k, v in data.items():
            if file_format == 'export':
                fh.write('export ' + k.strip()+'='+'\''+v.strip()+'\'\n')
            else:
                fh.write(k.strip()+'='+'\''+v.strip()+'\'\n')
    fh.close()