class TaskDefinition(object): pass


class FetchBnfCodes(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'bnf_codes'


class FetchAdqs(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'adqs'


class FetchPatientListSize(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'patient_list_size'


class FetchCcgBoundaries(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'ccg_boundaries'


class FetchPatientListWeightings(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'patient_list_weightings'


class FetchCcgDetails(TaskDefinition):
    task_type = 'fetcher'
    source = 'ccg_details'

    def run(self):
        '''org_codes.py --ccg'''


class FetchPracticeDetails(TaskDefinition):
    task_type = 'fetcher'
    source = 'practice_details'

    def run(self):
        '''org_codes.py --practice'''


class ImportBnfCodes(TaskDefinition):
    task_type = 'importer'
    source = 'bnf_codes'
    dependencies = [
        FetchBnfCodes,
    ]

    def run(self):
        '''import_bnf_codes --filename bnf_codes.csv'''


class ImportCcgBoundaries(TaskDefinition):
    task_type = 'importer'
    source = 'ccg_boundaries'
    dependencies = [
        FetchCcgBoundaries,
    ]

    def run(self):
        '''import_ccg_boundaries --filename ccg_boundaries.*\.kml'''


class ImportCcgDetails(TaskDefinition):
    task_type = 'importer'
    source = 'ccg_details'
    dependencies = [
        FetchCcgDetails,
        ImportCcgBoundaries,
    ]

    def run(self):
        '''import_org_names --ccg eccg.csv'''


class FetchPrescribing(TaskDefinition):
    task_type = 'fetcher'
    source = 'prescribing'

    def run(self):
        '''hscic_prescribing.py --most_recent_date'''


class ImportAdqs(TaskDefinition):
    task_type = 'importer'
    source = 'adqs'
    dependencies = [
        FetchAdqs,
        ImportBnfCodes,
    ]

    def run(self):
        '''import_adqs --filename adqs_.*csv'''


class ImportPatientListWeightings(TaskDefinition):
    task_type = 'importer'
    source = 'patient_list_weightings'
    dependencies = [
        FetchPatientListWeightings,
    ]

    def run(self):
        '''calculate_star_pu_weights --filename prescribing_units.xlsx'''


class ImportPracticeDetails(TaskDefinition):
    task_type = 'importer'
    source = 'practice_details'
    dependencies = [
        FetchPracticeDetails,
        ImportCcgDetails,
        ImportPatientListWeightings,
    ]

    def run(self):
        '''import_practices --epraccur epraccur.csv'''


class FetchNhsPostcodeFile(TaskDefinition):
    task_type = 'fetcher'
    source = 'nhs_postcode_file'

    def run(self):
        '''org_codes.py --postcode'''


class ImportNhsPostcodeFile(TaskDefinition):
    task_type = 'importer'
    source = 'nhs_postcode_file'
    dependencies = [
        FetchNhsPostcodeFile,
        ImportPracticeDetails,
    ]

    def run(self):
        '''geocode_practices --filename gridall\.csv'''


class ImportPrescribing0(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        FetchPrescribing,
        ImportBnfCodes,
        ImportAdqs,
        ImportNhsPostcodeFile,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_hscic_chemicals --chem_file T\d+CHEM.*\.CSV'''


class ImportPrescribing1(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        FetchPrescribing,
        ImportPrescribing0,
        ImportBnfCodes,
        ImportAdqs,
        ImportNhsPostcodeFile,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_practices --hscic_address T\d+ADDR.*\.CSV'''


class ImportPrescribing2(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        FetchPrescribing,
        ImportPrescribing0,
        ImportPrescribing1,
        ImportBnfCodes,
        ImportAdqs,
        ImportNhsPostcodeFile,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''convert_hscic_prescribing --filename T\d+PDPI.*BNFT\.CSV'''


class ImportPrescribing3(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        FetchPrescribing,
        ImportPrescribing0,
        ImportPrescribing1,
        ImportPrescribing2,
        ImportBnfCodes,
        ImportAdqs,
        ImportNhsPostcodeFile,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_hscic_prescribing --filename T\d+PDPI.*_formatted\.CSV'''


class ImportDispensingPractices(TaskDefinition):
    task_type = 'importer'
    source = 'dispensing_practices'
    dependencies = [
        ImportPrescribing0,
        ImportPrescribing1,
        ImportPrescribing2,
        ImportPrescribing3,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_practice_dispensing_status --filename dispensing_practices.*\.csv'''


class ImportPatientListSize(TaskDefinition):
    task_type = 'importer'
    source = 'patient_list_size'
    dependencies = [
        FetchPatientListSize,
        ImportPrescribing0,
        ImportPrescribing1,
        ImportPrescribing2,
        ImportPrescribing3,
        ImportPracticeDetails,
        ImportPatientListWeightings,
    ]

    def run(self):
        '''import_list_sizes --filename Patient_List_Size.*csv'''


class UploadToBigquery(TaskDefinition):
    task_type = 'other'
    dependencies = [
        ImportPatientListSize,
        ImportPrescribing0,
        ImportPrescribing1,
        ImportPrescribing2,
        ImportPrescribing3,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''runner:bigquery_upload'''


class Measures0(TaskDefinition):
    task_type = 'other'
    dependencies = [
        UploadToBigquery,
    ]

    def run(self):
        '''import_measures --definitions_only'''


class Measures1(TaskDefinition):
    task_type = 'other'
    dependencies = [
        UploadToBigquery,
        Measures0,
    ]

    def run(self):
        '''import_measures'''


class RefreshViews(TaskDefinition):
    task_type = 'other'
    dependencies = [
        UploadToBigquery,
    ]

    def run(self):
        '''create_views'''
