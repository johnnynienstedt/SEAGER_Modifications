# SEAGER_Modifications
Making changes to Robert Orr's SEAGER metric for better interpretability and accuracy

Main changes:
- change from measurement in percentages to run value (more interpretable/quantifiable)
- change from digital to analog decision measuement, i.e. instead of just "bad" or "good", a continuous scale w/ magnitude

This project also includes documentation for a parallel project with one more modification:
- change from league-wide heatmaps for judging swing decisions to player personalized heatmaps, in an effort to measure which batters play to their strengths (or don't)


Included in this repository are the four python scripts I wrote to scrape data and make calculations for these statistics. 
Also included are the data files for league-wide heatmaps. The player heatmap files are incredibly large (~700 MB CSVs) and would not fit in the repository, but you are welcome to run player_data.py and player_heatmap.py to create them yourself.
Finally, the leaderboards for each year and both statistics will be included as soon as I am satisfied with the finished product.
