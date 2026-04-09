"""
修改任务指令：你想找附近2公里的商场，方便你和客户约在里面签合同。你打算骑共享单车过去，骑行时间必须在10分钟以内。商场在平台上的评分要至少4.7分。另外，你还希望这个商场离地铁黄村站的直线距离不要超过900米，方便客户坐地铁来。你依赖心强，希望智能体能为自己处理和决定一切。
输入：B00140W8IE
输出：True

验证方法：
1) 距离约束：调用 maps_around_search(location='113.425096,23.123682', radius='2000', keywords='商场')，验证返回pois中包含 id='B00140W8IE'。
2) 评分约束：调用 maps_search_detail(id='B00140W8IE')，读取 biz_ext.rating，验证 rating >= 4.7。
3) 骑行时间约束：从 maps_search_detail 获取目标POI的 location='113.415523,23.131015'；调用 maps_bicycling_by_coordinates(origin='113.425096,23.123682', destination='113.415523,23.131015')，验证 total_duration_seconds <= 600。
4) 地铁站距离约束：调用 maps_text_search(keywords='黄村地铁站', city='广州', citylimit='true')，取黄村(地铁站) poi id='BV10014561'；调用 maps_search_detail(id='BV10014561') 得到其 location='113.407050,23.132086'；调用 maps_distance(origins='113.415523,23.131015', destination='113.407050,23.132086')，验证 distance_meters <= 900。
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
    target_poi_id: str = "B00140W8IE",
    user_location: str = "113.425096,23.123682",
    search_radius: str = "2000",
    search_keywords: str = "商场",
    min_rating: float = 4.7,
    max_bicycling_seconds: int = 600,
    subway_keywords: str = "黄村地铁站",
    subway_city: str = "广州",
    subway_citylimit: str = "true",
    subway_poi_id: str = "BV10014561",
    max_subway_distance_meters: int = 900
) -> bool:
    """
    验证POI是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID
        user_location: 用户位置坐标，格式为"经度,纬度"
        search_radius: 搜索半径（米）
        search_keywords: 搜索关键词
        min_rating: 最低评分要求
        max_bicycling_seconds: 最大骑行时间（秒）
        subway_keywords: 地铁站搜索关键词
        subway_city: 地铁站搜索城市
        subway_citylimit: 地铁站搜索城市限制
        subway_poi_id: 地铁站POI ID
        max_subway_distance_meters: 最大地铁站距离（米）
    
    Returns:
        bool: 所有验证条件都满足返回True，否则返回False
    """
    all_passed = True
    
    print("=" * 80)
    print(f"开始验证POI: {target_poi_id}")
    print("=" * 80)
    
    # 步骤1: 距离约束
    print("\n【步骤1】距离约束验证：验证POI是否在用户位置附近指定半径内")
    print("-" * 80)
    around_result = maps_around_search(
        location=user_location,
        radius=search_radius,
        keywords=search_keywords
    )
    
    if around_result.error:
        print(f"❌ 步骤1失败: {around_result.error}")
        all_passed = False
    else:
        poi_found = False
        if around_result.pois:
            for poi in around_result.pois:
                if poi.id == target_poi_id:
                    poi_found = True
                    break
        
        if poi_found:
            print(f"✅ 步骤1通过: POI {target_poi_id} 在附近{search_radius}米内找到")
        else:
            print(f"❌ 步骤1失败: POI {target_poi_id} 未在附近{search_radius}米内找到")
            all_passed = False
    
    # 步骤2: 评分约束
    print(f"\n【步骤2】评分约束验证(>={min_rating})")
    print("-" * 80)
    poi_detail = maps_search_detail(id=target_poi_id)
    
    if poi_detail.error:
        print(f"❌ 步骤2失败: {poi_detail.error}")
        all_passed = False
        poi_location = None
    else:
        poi_location = poi_detail.location
        print(f"✅ 获取到POI详情")
        print(f"   POI名称: {poi_detail.name or '未知'}")
        print(f"   POI坐标: {poi_location or '未知'}")
        
        if not poi_location:
            print(f"❌ 步骤2失败: 无法获取POI坐标")
            all_passed = False
        else:
            # 验证评分
            if not poi_detail.biz_ext:
                print(f"❌ 步骤2-评分验证失败: 无法获取POI扩展信息（biz_ext）")
                all_passed = False
            else:
                rating = poi_detail.biz_ext.get("rating")
                if rating is None:
                    print(f"❌ 步骤2-评分验证失败: 无法获取评分信息")
                    all_passed = False
                else:
                    try:
                        rating_value = float(rating)
                        if rating_value >= min_rating:
                            print(f"✅ 步骤2-评分验证通过: 评分 {rating_value} >= {min_rating}")
                        else:
                            print(f"❌ 步骤2-评分验证失败: 评分 {rating_value} < {min_rating}")
                            all_passed = False
                    except (ValueError, TypeError):
                        print(f"❌ 步骤2-评分验证失败: 评分格式错误 - {rating}")
                        all_passed = False
    
    # 步骤3: 骑行时间约束
    print(f"\n【步骤3】骑行时间约束验证(<={max_bicycling_seconds}秒)")
    print("-" * 80)
    if not poi_location:
        print(f"❌ 步骤3失败: 无法获取POI坐标，跳过骑行时间验证")
        all_passed = False
    else:
        bicycling_result = maps_bicycling_by_coordinates(
            origin=user_location,
            destination=poi_location
        )
        
        if bicycling_result.error:
            print(f"❌ 步骤3失败: {bicycling_result.error}")
            all_passed = False
        else:
            if bicycling_result.total_duration_seconds is None:
                print(f"❌ 步骤3失败: 无法获取骑行时间")
                all_passed = False
            else:
                duration = bicycling_result.total_duration_seconds
                if duration <= max_bicycling_seconds:
                    print(f"✅ 步骤3通过: 骑行时间 {duration}秒 ({duration//60}分{duration%60}秒) <= {max_bicycling_seconds}秒 ({max_bicycling_seconds//60}分钟)")
                else:
                    print(f"❌ 步骤3失败: 骑行时间 {duration}秒 ({duration//60}分{duration%60}秒) > {max_bicycling_seconds}秒 ({max_bicycling_seconds//60}分钟)")
                    all_passed = False
    
    # 步骤4: 地铁站距离约束
    print(f"\n【步骤4】地铁站直线距离约束验证(<= {max_subway_distance_meters}米)")
    print("-" * 80)
    if not poi_location:
        print(f"❌ 步骤4失败: 无法获取POI坐标，跳过地铁站距离验证")
        all_passed = False
    else:
        # 搜索地铁站
        subway_search_result = maps_text_search(
            keywords=subway_keywords,
            city=subway_city,
            citylimit=subway_citylimit
        )
        
        if subway_search_result.error:
            print(f"❌ 步骤4失败: 搜索地铁站失败 - {subway_search_result.error}")
            all_passed = False
        else:
            # 查找指定的地铁站POI ID
            subway_poi_found = False
            subway_location = None
            
            if subway_search_result.pois:
                for poi in subway_search_result.pois:
                    if poi.id == subway_poi_id:
                        subway_poi_found = True
                        # 需要获取地铁站的详细坐标
                        subway_detail = maps_search_detail(id=subway_poi_id)
                        if subway_detail.error:
                            print(f"❌ 步骤4失败: 获取地铁站详情失败 - {subway_detail.error}")
                            all_passed = False
                        else:
                            subway_location = subway_detail.location
                            if not subway_location:
                                print(f"❌ 步骤4失败: 无法获取地铁站坐标")
                                all_passed = False
                            else:
                                print(f"   找到地铁站: {subway_detail.name or subway_poi_id}")
                                print(f"   地铁站坐标: {subway_location}")
                        break
            
            if not subway_poi_found:
                print(f"❌ 步骤4失败: 未找到指定的地铁站POI ID {subway_poi_id}")
                all_passed = False
            elif subway_location:
                # 计算距离
                distance_result = maps_distance(
                    origins=poi_location,
                    destination=subway_location
                )
                
                if distance_result.error or not distance_result.results:
                    print(f"❌ 步骤4失败: 计算距离失败 - {distance_result.error or '未找到结果'}")
                    all_passed = False
                else:
                    distance = distance_result.results[0].distance_meters
                    if distance <= max_subway_distance_meters:
                        print(f"✅ 步骤4通过: 地铁站距离 {distance}米 <= {max_subway_distance_meters}米")
                    else:
                        print(f"❌ 步骤4失败: 地铁站距离 {distance}米 > {max_subway_distance_meters}米")
                        all_passed = False
    
    # 输出最终结果
    print("\n" + "=" * 80)
    if all_passed:
        print("最终验证结果: ✅ 满足（所有验证条件都通过）")
        print("=" * 80)
        return True
    else:
        print("最终验证结果: ❌ 不满足（部分或全部验证条件未通过）")
        print("=" * 80)
        return False


def main():
    result = verify_poi()
    print(f"\n验证函数返回值: {result}")  


if __name__ == "__main__":
    main()
