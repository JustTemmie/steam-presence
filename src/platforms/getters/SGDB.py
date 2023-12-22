
def getImageFromSGDB(loops=0):
    global coverImage
    global coverImageText
    
    log("searching for an icon using the SGDB")
    # searches SGDB for the game you're playing
    results = sgdb.search_game(gameName)
    
    if len(results) == 0:
        log(f"could not find anything on SGDB")
        return

    
    log(f"found the game {results[0]} on SGDB")
    gridAppID = results[0].id
    
    # searches for icons
    gridIcons = sgdb.get_icons_by_gameid(game_ids=[gridAppID])
    
    # makes sure anything was returned at all
    if gridIcons != None:
    
        # throws the icons into a dictionary with the required information, then sorts them using the icon height
        gridIconsDict = {}
        for i, gridIcon in enumerate(gridIcons):
            gridIconsDict[i] = [gridIcon.height, gridIcon._nsfw, gridIcon.url, gridIcon.mime, gridIcon.author.name, gridIcon.id]
        
        gridIconsDict = (sorted(gridIconsDict.items(), key=lambda x:x[1], reverse=True))
        
        
        # does a couple checks before making it the cover image
        for i in range(0, len(gridIconsDict)):
            entry = gridIconsDict[i][1]
            # makes sure image is not NSFW
            if entry[1] == False:
                # makes sure it's not an .ico file - discord cannot display these
                if entry[3] == "image/png":
                    # sets the link, and gives credit to the artist if anyone hovers over the icon
                    coverImage = entry[2]
                    coverImageText = f"Art by {entry[4]} on SteamGrid DB"
                    log("successfully retrived icon from SGDB")
                    # saves this data to disk
                    with open(f'{dirname(abspath(__file__))}/data/icons.txt', 'a') as icons:
                        icons.write(f"{gameName.lower()}={coverImage}||{coverImageText}\n")
                        icons.close()
                    return
        
        log("failed, trying to load from the website directly")
        # if the game doesn't have any .png files for the game, try to web scrape them from the site
        for i in range(0, len(gridIconsDict)):
            entry = gridIconsDict[i][1]
            # makes sure image is not NSFW
            if entry[1] == False:
                URL = f"https://www.steamgriddb.com/icon/{entry[5]}"
                logDebug("getting image from SGDB's website")
                page = makeWebRequest(URL)
                if page == "error":
                    return
                
                if page.status_code != 200:
                    error(f"status code {page.status_code} recieved when trying to web scrape SGDB, ignoring")
                    return

                # web scraping, this code is messy
                soup = BeautifulSoup(page.content, "html.parser")

                img = soup.find("meta", property="og:image")
                
                coverImage = img["content"]
                coverImageText = f"Art by {entry[4]} on SteamGrid DB"

                log("successfully retrived icon from SGDB")

                # saves data to disk
                with open(f'{dirname(abspath(__file__))}/data/icons.txt', 'a') as icons:
                    icons.write(f"{gameName.lower()}={coverImage}||{coverImageText}\n")
                    icons.close()
                return
        
        log("failed to fetch icon from SGDB")
    
    else:
        log(f"SGDB doesn't seem to have any entries for {gameName}")