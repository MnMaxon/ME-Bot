import dataclasses
from typing import Collection, Any, List

from pandas import DataFrame
import pandas as pd

OPTION_DISABLED = "disabled_option"


@dataclasses.dataclass
class FilterOption:
    value: Any
    label: str = None
    selected_value: int = 0
    default_value: int = 0

    def get_label(self):
        if self.label is not None:
            return self.label
        return self.value


@dataclasses.dataclass
class DisabledOption(FilterOption):
    label: str = "Disabled"
    value: Any = OPTION_DISABLED


@dataclasses.dataclass
class DataFilter:
    options: List[FilterOption] = dataclasses.field(default_factory=list)
    col_name: str = None
    label: str = None
    selected_index = 0
    default_index = 0

    def get_mask(self, df) -> pd.Series or bool:
        return df is not None  # Should return True - override for a boolean mask

    async def filter(self, df: DataFrame):
        mask = await self.get_mask(df)
        return df[mask]

    def get_column(self, df) -> pd.Series:
        self.validate_col(df)
        return df[self.col_name]

    def validate_col(self, df):
        if self.col_name is None:
            raise ValueError("Column name not set")
        elif self.col_name not in df.columns:
            raise ValueError(f"Column {self.col_name} not in DataFrame")

    def get_label(self):
        if self.label is not None:
            return self.label
        if self.col_name is not None:
            return self.col_name
        return self.__class__.__name__

    def get_selected_option(self):
        return self.get_options()[self.selected_index]

    def get_options(self):
        return self.options


@dataclasses.dataclass
class InverseFilter(DataFilter):
    @staticmethod
    def translate_option(val: bool or None):
        if val is None:
            return 2
        if val:
            return 1
        return 0

    def __init__(
        self,
        label=None,
        false_label: str = "False",
        true_label: str = "True",
        disabled_label: str = "None",
        options=None,
        default_index: bool or int or None = 0,
        selected_index: bool or int or None or str = "default",
        allow_disable=True,
        **kwargs,
    ):
        default_index = self.translate_option(default_index)
        if selected_index == "default":
            selected_index = default_index
        else:
            selected_index = self.translate_option(selected_index)
        if options is None:
            options = [
                FilterOption(value=False, label=false_label),
                FilterOption(value=True, label=true_label),
            ]
            if allow_disable:
                options.append(DisabledOption(label=disabled_label))
        super().__init__(
            label=label,
            default_index=default_index,
            selected_index=selected_index,
            options=options,
            **kwargs,
        )

    def get_mask(self, df: DataFrame):
        val = self.get_selected_option().value
        if val == OPTION_DISABLED:
            return True
        elif val:
            return self.get_truth_mask(df)
        return ~self.get_truth_mask(df)

    def get_truth_mask(self, df: DataFrame):
        raise NotImplementedError("truth mask should be overridden")


@dataclasses.dataclass
class IsNullFilter(InverseFilter):
    col_name: str
    false_label: str = "Not Null"
    true_label: str = "Is Null"
    disabled_label: str = "Any"
    label = "Null Filter"

    def get_truth_mask(self, df: DataFrame):
        return self.get_column(df).isnull()


@dataclasses.dataclass
class FilterManager:
    filters: List[DataFilter] = dataclasses.field(default_factory=list)

    def get_filter_dict(self):
        filter_dict = {}
        for f in self.filters:
            if f.get_label() not in filter_dict:
                filter_dict[f.get_label()] = []
            filter_dict[f.get_label()].append(f)
        return filter_dict

    def filter(self, df: DataFrame):
        for f in self.filters:
            if (
                len(f.get_options()) > 0
                and f.get_selected_option().value != OPTION_DISABLED
            ):
                df = f.filter(df)
        return df
