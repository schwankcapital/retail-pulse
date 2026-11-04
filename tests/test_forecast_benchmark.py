import numpy as np
import pandas as pd
import pytest

from retail_pulse.forecast_benchmark import (
    _bound, _fold, calibration_quantile, choose_candidate, exposure_profile,
    measured_frame, predict_fixed_origin, score,
)


def history(n=35,qty=.125,flags=None):
    return pd.DataFrame([dict(sku='real-1',date=d,sales=qty*16,hourly_sales=np.repeat(qty,16),
                             stock_flags=np.zeros(16,dtype=int) if flags is None else np.array(flags))
                         for d in pd.date_range('2024-01-01',periods=n)])


def test_preserves_fractional_source_quantities():
    raw=pd.DataFrame([dict(product_id=1,dt='2024-01-01',hours_sale=[.0125]*24,hours_stock_status=[0]*24)])
    f=measured_frame(raw)
    assert f.sales.iloc[0]==pytest.approx(.2)
    assert f.available_hours.iloc[0]==16


def test_forecast_origin_excludes_intermediate_targets():
    past=history();dates=pd.date_range('2024-02-05',periods=7)
    prediction=predict_fixed_origin(past,dates,'seasonal7')
    assert np.all(prediction==2)
    with pytest.raises(ValueError):predict_fixed_origin(past,list(past.date.tail(7)),'mean28')


def test_censored_hours_do_not_lower_full_availability_rate():
    available=history();censored=history(flags=[0]*8+[1]*8)
    censored['hourly_sales']=[np.r_[np.repeat(.125,8),np.zeros(8)] for _ in range(len(censored))]
    censored['sales']=1.
    full=exposure_profile(available);limited=exposure_profile(censored)
    assert limited['full_available_daily']==pytest.approx(full['full_available_daily'])
    assert limited['recorded_daily']==pytest.approx(1.)
    assert limited['expected_available_hours']==pytest.approx(8.)


def test_publisher_flag_conflicts_are_excluded_from_rate_fit():
    f=history(flags=[0]*8+[1]*8)
    f['hourly_sales']=[np.r_[np.repeat(.125,8),np.repeat(100.,8)] for _ in range(len(f))]
    profile=exposure_profile(f)
    assert profile['full_available_daily']==pytest.approx(2.)
    assert profile['excluded_conflict_quantity']==pytest.approx(28000.)


def test_selection_only_uses_seven_day_validation():
    metrics={'a':{'7':{'wape':.2},'1':{'wape':.9}},'b':{'7':{'wape':.3},'1':{'wape':.1}}}
    assert choose_candidate(metrics)=='a'


def test_interval_quantile_is_calibration_only_and_nonnegative():
    records=[dict(actual=i,predicted=0.,scale=1.) for i in range(10)]
    q=calibration_quantile(records,.8)
    assert q==8
    assert _bound(1.,1.,q)==(0.,9.)


def test_horizon_sums_match_fixed_origin_predictions():
    past=history();target=history(42).tail(7)
    result=_fold(past,target,['mean28'])['mean28']
    assert result['1'][0]['predicted']==2
    assert result['3'][0]['predicted']==6
    assert result['7'][0]['predicted']==14


def test_sparse_series_and_zero_denominator_are_explicit():
    past=history(qty=0.)
    assert np.all(predict_fixed_origin(past,pd.date_range('2024-02-05',periods=7),'tsb_slow')==0)
    assert score([0.],[0.])['wape'] is None
