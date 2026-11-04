from retail_pulse.config import Settings
from retail_pulse.visual_grounding import prepare_visual_grounding

if __name__=='__main__':
    report=prepare_visual_grounding(Settings.from_env())
    print(report['completed_clips'],'clips;',report['total_box_records'],'actual SAM box records')
