"""
Mixins for adding Excel export capability to views.
"""

from rest_framework.permissions import IsAuthenticated


class ExcelExportMixin:
    """Mixin to add Excel export to list views."""

    export_columns = []  # List of (key, header, width) tuples
    export_filename = 'export.xlsx'
    export_sheet_name = 'بيانات'

    def get_export_data(self):
        """Override to customize export data source."""
        return self.filter_queryset(self.get_queryset())

    def export_excel(self, request):
        """Generate Excel file from queryset."""
        from core.utils import export_to_excel, prepare_export_data

        queryset = self.get_export_data()
        fields_map = {col[0]: col[0] for col in self.export_columns}
        data = prepare_export_data(queryset, fields_map)

        return export_to_excel(
            data=data,
            columns=self.export_columns,
            sheet_name=self.export_sheet_name,
            filename=self.export_filename,
        )
