import glob
import pandas as pd
from typing import Union, List, Literal, Any, Dict
import numpy as np
from abc import ABC

class MMLUDataset(ABC):
    def __init__(self,
        split: Union[Literal['dev'], Literal['val'], Literal['test']],
        ) -> None:

        self._split = split

        data_path = f"PruneComm/data/dataset/MMLU/data/{self._split}/"
        self._total_df: pd.DataFrame = self._load_data(data_path)

    @staticmethod
    def get_domain() -> str:
        return 'mmlu'

    @staticmethod
    def _load_data(
        data_path: str,
        ) -> pd.DataFrame:

        rng = np.random.default_rng(888)

        csv_paths = glob.glob(data_path + "*.csv")
        csv_paths = sorted(csv_paths)
        print("Number of topics: ", len(csv_paths))

        names = ['question', 'A', 'B', 'C', 'D', 'correct_answer']

        total_df = pd.DataFrame(columns=names)
        for path in csv_paths:
            single_df = pd.read_csv(path, header=None,
                            names=names,encoding='utf-8')
            total_df = pd.concat([total_df, single_df])

        total_df = total_df.reset_index(drop=True)

        # Pseudorandom shuffle
        total_df = total_df.reindex(rng.permutation(total_df.index))

        print("Total number of questions: ", len(total_df))

        return total_df

    @property
    def split(self) -> str:
        return self._split

    def __len__(self) -> int:
        return len(self._total_df)

    def __getitem__(self, index: int) -> pd.DataFrame:
        record = self._total_df.iloc[index]
        assert isinstance(record, pd.DataFrame) or isinstance(record, pd.Series)
        return record

    @staticmethod
    def record_to_input(record: pd.DataFrame) -> Dict[str, Any]:
        question = str(record["question"]).strip()

        options = {
            "A": str(record["A"]).strip(),
            "B": str(record["B"]).strip(),
            "C": str(record["C"]).strip(),
            "D": str(record["D"]).strip(),
        }

        # 对齐选项（让控制台更整齐）
        max_len = max(len(opt) for opt in options.values())
        
        formatted_options = "\n".join(
            [f"  {k}. {v}" for k, v in options.items()]
        )

        task = (
            "=== Question ===\n"
            f"{question}\n\n"
            "=== Options ===\n"
            f"{formatted_options}\n"
        )

        return {"task": task}

    def postprocess_answer(self, answer: Union[str, List[str]]) -> str:
        if isinstance(answer, list):
            if len(answer) > 0:
                answer = answer[0]
            else:
                answer = ""
        if not isinstance(answer, str):
            raise Exception("Expected string")
        if len(answer) > 0:
            ans_pos = answer.find("answer is")
            if ans_pos != -1:
                answer = answer[ans_pos+len("answer is"):].strip(":").strip().strip("Option").strip()
            answer = answer[0] # Try to format the answer by taking the first letter
        return answer

    @staticmethod
    def record_to_target_answer(record: pd.DataFrame) -> str:
        correct_answer = record['correct_answer']
        assert isinstance(correct_answer, str), (
            f"String expected but got {correct_answer} "
            f"of type {type(correct_answer)} (2)" \
            f" record={record}")
        return correct_answer
