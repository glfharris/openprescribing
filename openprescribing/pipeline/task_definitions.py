class TaskDefinition(object): pass


class FetchBnfCodes(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'bnf_codes'


class FetchAdqs(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'adqs'


class FetchCcgBoundaries(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'ccg_boundaries'


class FetchPatientListWeightings(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'patient_list_weightings'


class FetchPatientListSize(TaskDefinition):
    task_type = 'fetcher'
    source = 'patient_list_size'

    def run(self):
        '''hscic_list_sizes.py'''


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


class FetchPrescribingMetadata(TaskDefinition):
    task_type = 'fetcher'
    source = 'prescribing_metadata'

    def run(self):
        '''hscic_prescribing.py --most_recent_date'''


class FetchPrescribing(TaskDefinition):
    task_type = 'manual_fetcher'
    source = 'prescribing'


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


class ImportHscicChemicals(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing_metadata'
    dependencies = [
        FetchPrescribingMetadata,
    ]

    def run(self):
        '''import_hscic_chemicals --chem_file T\d+CHEM.*\.CSV'''


class ImportHscicPractices(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing_metadata'
    dependencies = [
        FetchPrescribingMetadata,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_practices --hscic_address T\d+ADDR.*\.CSV'''


class ConvertHscicPrescriptions(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        FetchPrescribing,
    ]

    def run(self):
        '''convert_hscic_prescribing --filename .*Detailed_Prescribing_Information.csv'''


class ImportPrescriptions(TaskDefinition):
    task_type = 'importer'
    source = 'prescribing'
    dependencies = [
        ImportHscicPractices,
        ConvertHscicPrescriptions,
        ImportBnfCodes,
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_hscic_prescribing --filename .*Detailed_Prescribing_Information_formatted.CSV'''


class ImportDispensingPractices(TaskDefinition):
    task_type = 'importer'
    source = 'dispensing_practices'
    dependencies = [
        ImportHscicPractices,
        ImportPracticeDetails,
    ]

    def run(self):
        '''import_practice_dispensing_status --filename dispensing_practices.*\.csv'''


class ImportPatientListSize(TaskDefinition):
    task_type = 'importer'
    source = 'patient_list_size'
    dependencies = [
        FetchPatientListSize,
        ImportHscicPractices,
        ImportPracticeDetails,
        ImportPatientListWeightings,
    ]

    def run(self):
        '''import_list_sizes --filename patient_list_size_new.csv'''


class UploadToBigquery(TaskDefinition):
    task_type = 'other'
    dependencies = [
        ImportPatientListSize,
        ImportHscicPractices,
        ImportPrescriptions,  # Not sure whether this is a dependency
        ImportCcgDetails,
        ImportPracticeDetails,
    ]

    def run(self):
        '''runner:bigquery_upload'''


class ImportMeasureDefinitions(TaskDefinition):
    task_type = 'other'
    dependencies = [
        # Since this reads from data in measure_definitions directory,
        # presumably we should re-run this when that data is updated.  However,
        # there is no fetcher for this data.
    ]

    def run(self):
        '''import_measures --definitions_only'''


class ImportMeasures(TaskDefinition):
    task_type = 'other'
    dependencies = [
        UploadToBigquery,
        ImportMeasureDefinitions,
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
