"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
根据给定的验证方法验证POI是否符合要求。
输入：B0G04S6ZV8
输出：True

验证方法：
1) 距离约束（附近20公里内）：以用户坐标79.889578,40.693541为中心，调用maps_around_search(location='79.889578,40.693541', radius='20000', keywords='酒店')，验证返回pois列表中包含目标poi_id=B0G04S6ZV8。
2) 评分约束（评分不低于4.3）：调用maps_search_detail(id='B0G04S6ZV8')，读取biz_ext.rating，验证其数值>=4.3。
3) 步行时间约束（步行不超过15分钟）：从maps_search_detail获取目标POI坐标location='79.895636,40.686122'，调用maps_walking_by_coordinates(origin='79.889578,40.693541', destination='79.895636,40.686122')，验证total_duration_seconds <= 900。
4) 周边无地铁站约束（800米内无地铁站）：调用maps_around_search(location='79.895636,40.686122', radius='800', keywords='地铁站')，验证返回pois为空或pois长度为0。
"""
def verify_poi(
    target_poi_id: str = "B0G04S6ZV8",
    user_location: str = "79.889578,40.693541",
    search_radius: str = "20000",
    search_keywords: str = "酒店",
    max_walking_seconds: int = 900,
    metro_search_radius: str = "800",
    metro_keywords: str = "地铁站",
    min_rating: float = 4.3
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID，默认值为 "B0G04S6ZV8"
        user_location: 用户位置坐标，格式为"经度,纬度"，默认值为 "79.889578,40.693541"
        search_radius: 搜索半径（米），默认值为 "20000"
        search_keywords: 搜索关键词，默认值为 "酒店"
        max_walking_seconds: 最大步行时间（秒），默认值为 900（15分钟）
        metro_search_radius: 地铁站搜索半径（米），默认值为 "800"
        metro_keywords: 地铁站搜索关键词，默认值为 "地铁站"
        min_rating: 最小评分，默认值为 4.3
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    # 步骤1：距离约束（附近20公里内）
    print(f"步骤1：验证目标是否在附近{int(search_radius)/1000}公里内")
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    
    if around_result.error:
        print(f"  验证失败：周边搜索出错 - {around_result.error}")
        return False
    
    if not around_result.pois:
        print(f"  验证失败：未找到任何POI")
        return False
    
    # 检查返回的pois列表中是否包含target_poi_id
    poi_ids = [poi.id for poi in around_result.pois]
    if target_poi_id in poi_ids:
        print(f"  验证通过：POI {target_poi_id} 在附近{int(search_radius)/1000}公里内")
    else:
        print(f"  验证失败：POI {target_poi_id} 不在附近{int(search_radius)/1000}公里内")
        all_passed = False
    
    # 步骤2：评分约束（评分不低于4.3）
    print(f"步骤2：验证评分不低于{min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"  验证失败：获取POI详情出错 - {poi_detail.error}")
        return False
    
    if not poi_detail.biz_ext:
        print(f"  验证失败：无法获取POI扩展信息（biz_ext）")
        all_passed = False
    else:
        rating = poi_detail.biz_ext.get("rating")
        if rating is None:
            print(f"  验证失败：无法获取评分信息")
            all_passed = False
        else:
            try:
                rating_value = float(rating)
                if rating_value >= min_rating:
                    print(f"  验证通过：评分 {rating_value} >= {min_rating}")
                else:
                    print(f"  验证失败：评分 {rating_value} < {min_rating}")
                    all_passed = False
            except (ValueError, TypeError):
                print(f"  验证失败：评分格式错误 - {rating}")
                all_passed = False
    
    # 步骤3：步行时间约束（步行不超过15分钟）
    print(f"步骤3：验证步行不超过{max_walking_seconds//60}分钟")
    
    if not poi_detail.location:
        print(f"  验证失败：无法获取POI坐标")
        return False
    
    poi_location = poi_detail.location
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
    
    if walking_result.error:
        print(f"  验证失败：步行路线规划出错 - {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  验证失败：无法获取步行时长")
        return False
    
    t_walk_seconds = walking_result.total_duration_seconds
    
    if t_walk_seconds <= max_walking_seconds:
        print(f"  验证通过：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 <= {max_walking_seconds//60}分钟")
    else:
        print(f"  验证失败：步行时间 {t_walk_seconds//60}分{t_walk_seconds%60}秒 > {max_walking_seconds//60}分钟")
        all_passed = False
    
    # 步骤4：周边无地铁站约束（800米内无地铁站）
    print(f"步骤4：验证周边{int(metro_search_radius)}米内无地铁站")
    metro_around_result = maps_around_search(
        location=poi_location,
        radius=metro_search_radius,
        keywords=metro_keywords
    )
    
    if metro_around_result.error:
        print(f"  验证失败：地铁站周边搜索出错 - {metro_around_result.error}")
        return False
    
    # 验证返回pois为空或pois长度为0
    if not metro_around_result.pois or len(metro_around_result.pois) == 0:
        print(f"  验证通过：周边{int(metro_search_radius)}米内无地铁站")
    else:
        print(f"  验证失败：周边{int(metro_search_radius)}米内找到{len(metro_around_result.pois)}个地铁站")
        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '不通过'}")
    return result  


if __name__ == "__main__":
    main()
