import math
import pytest
from retail_pulse.visual_grounding import normalize_records,compare_review,EvidenceChallenge,validate_review

def test_sam_inclusive_pixels_project_to_right_camera_only():
    info={'fps':6.,'frame_count':30,'width':600,'height':600}
    records=[dict(frame_index=12,object_id=9,box=dict(x1=0,y1=0,x2=599,y2=599,w=600,h=600),confidence=.9)]
    out=normalize_records(records,info,'rank1')
    assert out[0]['time_seconds']==2
    assert out[0]['boxes'][0]['xyxy']==[.5,0.,1.,1.]
    assert out[0]['boxes'][0]['track_id']=='rank1:9'

def test_non_square_source_honors_letterbox():
    info={'fps':6.,'frame_count':30,'width':600,'height':300}
    records=[dict(frame_index=1,object_id=1,box=dict(x1=0,y1=0,x2=599,y2=299,w=600,h=300),confidence=None)]
    assert normalize_records(records,info,'rank0')[0]['boxes'][0]['xyxy']==[0.,.25,.5,.75]

def test_sam_frame_cannot_outlive_video():
    with pytest.raises(ValueError,match='frame index'):
        normalize_records([dict(frame_index=30)],{'frame_count':30},'rank1')

def test_geometry_is_not_a_transfer_confirmation():
    result=compare_review({'transfers':[{'action':'take','quantity_min':2,'quantity_max':2}]},
        {'action':'take','quantity_min':1,'quantity_max':1,'confidence':.9,'cross_view_consistency':'consistent'})
    assert result['requires_human_review'] and not result['count_agrees']
    assert result['verdict']=='REVIEW_REQUIRED'

def test_uncountable_or_occluded_review_is_not_zero():
    result=compare_review({'transfers':[{'action':'take','quantity_min':2,'quantity_max':2}]},
        {'action':'take','quantity_min':None,'quantity_max':None,'confidence':.9,'cross_view_consistency':'insufficient_visibility'})
    assert result['requires_human_review'] and result['second_pass_exact_transfer_count'] is None

def test_review_bounds_are_enforced():
    r=EvidenceChallenge(action='take',quantity_min=1,quantity_max=1,start_seconds=0,end_seconds=8,confidence=.9,
        left_view_evidence='visible',right_view_evidence='visible',cross_view_consistency='consistent',
        potential_failure_modes=[],human_review_question='Count?',limitations=[])
    with pytest.raises(ValueError,match='outside'):validate_review(r,5)
