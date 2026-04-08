"""
修改任务指令：你要找一个附近3公里以内的购物中心，准备买份礼物顺便办点事。你希望这个地方口碑要好一些，评分至少4.2分。你还得马上去济宁大安机场，所以从购物中心开车到机场的时间必须在70分钟以内。另外，你希望商场名字里要带“商场”两个字，方便你在电话里跟别人确认地点。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。
输入：B02190ACFK
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search(location=116.58024,35.413115 radius=3000 keywords=购物中心) 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 候选列表，验证 target_poi_id 在返回的 pois.id 中（验证“3公里内购物中心”）。
2) 用 maps_search_detail(id=target_poi_id) 获取 biz_ext.rating，验证评分 >= 4.2（验证“评分至少4.2分”）。
3) 用 maps_search_detail(id=target_poi_id) 获取 name，验证 name 包含“商场”（验证“名字里带商场”）。
4) 用(address=济宁大安机场 city=济宁) 获取机场坐标 location_airport。
5) 用 maps_driving_by_coordinates(origin=POI.location destination=location_airport) 获取 total_duration_seconds，验证 total_duration_seconds/60 <= 70（验证“到济宁大安机场70分钟内可到”）。
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
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = 'B02190ACFK',
    user_location: str = '116.58024,35.413115',
    radius: str = '3000',
    keywords: str = '购物中心',
    min_rating: float = 4.2,
    name_keyword: str = '商场',
    airport_address: str = '济宁大安机场',
    airport_city: str = '济宁',
    max_driving_minutes: int = 70
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 需要验证的POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        radius: 搜索半径（米），字符串格式
        keywords: 搜索关键词
        min_rating: 最低评分要求
        name_keyword: 名称中必须包含的关键词
        airport_address: 机场地址
        airport_city: 机场所在城市
        max_driving_minutes: 最大驾车时长（分钟）
    
    Returns:
        bool: True表示所有验证通过，False表示部分或全部验证失败
    """
    all_passed = True
    
    # 验证步骤1: 验证POI在用户位置3公里内且为购物中心
    print(f"验证步骤1: 验证POI在用户位置{radius}米内且为{keywords}")
    around_search_result = maps_around_search(
        location=user_location,
        radius=radius,
        keywords=keywords
    )
    
    if around_search_result.error:
        print(f"验证步骤1失败: {around_search_result.error}")
        all_passed = False
    elif not around_search_result.pois:
        print("验证步骤1失败: 未找到符合条件的POI")
        all_passed = False
    else:
        # 检查返回的POI列表中是否包含目标POI ID
        found = False
        for poi in around_search_result.pois:
            if poi.id == target_poi_id:
                found = True
                break
        
        if found:
            print(f"验证步骤1通过: 在{radius}米内找到目标{keywords}POI")
        else:
            print(f"验证步骤1失败: 在{radius}米内未找到目标{keywords}POI")
            all_passed = False
    
    # 验证步骤2: 获取POI详情，验证评分 >= 4.2
    print(f"验证步骤2: 获取POI详情并验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"验证步骤2失败: {poi_detail.error}")
        all_passed = False
    else:
        # 获取评分
        rating = None
        if poi_detail.biz_ext and isinstance(poi_detail.biz_ext, dict):
            rating_str = poi_detail.biz_ext.get('rating')
            if rating_str:
                try:
                    rating = float(rating_str)
                except (ValueError, TypeError):
                    pass
        
        if rating is None:
            print("验证步骤2失败: 未获取到POI评分")
            all_passed = False
        elif rating >= min_rating:
            print(f"验证步骤2通过: 评分 {rating} >= {min_rating}")
        else:
            print(f"验证步骤2失败: 评分 {rating} < {min_rating}")
            all_passed = False
    
    # 验证步骤3: 验证名称包含"商场"
    print(f"验证步骤3: 验证名称包含{name_keyword}")
    if poi_detail.error:
        print("验证步骤3失败: 无法获取POI详情（已在步骤2中失败）")
        all_passed = False
    else:
        poi_name = poi_detail.name
        if not poi_name:
            print("验证步骤3失败: 未获取到POI名称")
            all_passed = False
        elif name_keyword in poi_name:
            print(f"验证步骤3通过: 名称 '{poi_name}' 包含 '{name_keyword}'")
        else:
            print(f"验证步骤3失败: 名称 '{poi_name}' 不包含 '{name_keyword}'")
            all_passed = False
    
    # 验证步骤4: 获取机场坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    print(f"验证步骤4: 获取机场坐标（地址: {airport_address}, 城市: {airport_city}）")
    airport_text_result = maps_text_search(keywords=airport_address, city=airport_city)
    if airport_text_result.error:
        print(f"验证步骤4失败: {airport_text_result.error}")
        all_passed = False
    elif not airport_text_result.pois or len(airport_text_result.pois) == 0:
        print("验证步骤4失败: 未找到机场坐标")
        all_passed = False
    else:
        first_poi_id = airport_text_result.pois[0].id
        airport_detail_result = maps_search_detail(id=first_poi_id)
        if airport_detail_result.error:
            print(f"❌ 获取坐标失败: {airport_detail_result.error}")
            all_passed = False
        elif not airport_detail_result.location:
            print("❌ 未获取到坐标")
            all_passed = False
        else:
            location_airport = airport_detail_result.location
            print(f"验证步骤4通过: 获取到机场坐标 {location_airport}")
            
            # 验证步骤5: 验证驾车到机场的时间 <= 70分钟
            print(f"验证步骤5: 验证驾车到机场的时间 <= {max_driving_minutes}分钟")
            
            # 获取POI坐标
            if poi_detail.error or not poi_detail.location:
                print("验证步骤5失败: 无法获取POI坐标（已在步骤2中失败）")
                all_passed = False
            else:
                poi_location = poi_detail.location
                driving_result = maps_driving_by_coordinates(
                    origin=poi_location,
                    destination=location_airport
                )
                
                if driving_result.error:
                    print(f"验证步骤5失败: {driving_result.error}")
                    all_passed = False
                elif driving_result.total_duration_seconds is None:
                    print("验证步骤5失败: 未获取到驾车时长")
                    all_passed = False
                else:
                    driving_minutes = driving_result.total_duration_seconds / 60.0
                    if driving_minutes <= max_driving_minutes:
                        print(f"验证步骤5通过: 驾车时长 {driving_minutes:.1f}分钟 <= {max_driving_minutes}分钟")
                    else:
                        print(f"验证步骤5失败: 驾车时长 {driving_minutes:.1f}分钟 > {max_driving_minutes}分钟")
                        all_passed = False
    
    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result


if __name__ == "__main__":
    main()
