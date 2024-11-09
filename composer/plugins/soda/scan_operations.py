import logging as log
import os

def run_soda_scan(data_source, scan_name, checks_subpath = None):
    from soda.scan import Scan
    
    base_path = os.path.join(os.getcwd(), "gcs", "plugins", "soda")
    config_file = f"{base_path}/configuration.yml"
    checks_path = f"{base_path}/checks"
    if checks_subpath:
        checks_path += f"/{checks_subpath}"
    
    file_scan_path = f"{checks_path}/{scan_name}.yaml"
    
    log.info("-------------------------- Starting Soda Scan --------------------------")
    log.info(f"Data Source: {data_source}")
    log.info(f"Scan Name: {scan_name}")
    
    scan = Scan()
    scan.set_verbose()
    scan.add_configuration_yaml_file(config_file)
    scan.set_data_source_name(data_source)
    scan.add_sodacl_yaml_files(file_scan_path)
    scan.set_scan_definition_name(scan_name)

    result = scan.execute()
    log.info(scan.get_logs_text())

    if result != 0:
        raise ValueError('Soda Scan failed')

    return result