#===============================================================================
# Battle Info UI
#===============================================================================
class Battle::Scene
  #-----------------------------------------------------------------------------
  # Handles the controls for the Battle Info UI.
  #-----------------------------------------------------------------------------
  def pbOpenBattlerInfo(battler, battlers)
    return if @enhancedUIToggle != :battler
    ret = nil
    idx = 0
    battlerTotal = battlers.flatten
    for i in 0...battlerTotal.length
      idx = i if battler == battlerTotal[i]
    end
    maxSize = battlerTotal.length - 1
    idxEffect = 0
    effects = pbGetDisplayEffects(battler)
    effctSize = effects.length - 1
    pbUpdateBattlerInfo(battler, effects, idxEffect)
    cw = @sprites["fightWindow"]
    @sprites["leftarrow"].x = -2
    @sprites["leftarrow"].y = 71
    @sprites["leftarrow"].visible = true
    @sprites["rightarrow"].x = Graphics.width - 38
    @sprites["rightarrow"].y = 71
    @sprites["rightarrow"].visible = true
    loop do
      pbUpdate(cw)
      pbUpdateInfoSprites
      break if Input.trigger?(Input::BACK)
      if Input.trigger?(Input::LEFT)
        idx -= 1
        idx = maxSize if idx < 0
        doFullRefresh = true
      elsif Input.trigger?(Input::RIGHT)
        idx += 1
        idx = 0 if idx > maxSize
        doFullRefresh = true
      elsif Input.repeat?(Input::UP) && effects.length > 1
        idxEffect -= 1
        idxEffect = effctSize if idxEffect < 0
        doRefresh = true
      elsif	Input.repeat?(Input::DOWN) && effects.length > 1
        idxEffect += 1
        idxEffect = 0 if idxEffect > effctSize
        doRefresh = true
      elsif Input.trigger?(Input::JUMPDOWN)
        if cw.visible
          ret = 1
          break
        elsif @battle.pbCanUsePokeBall?(@sprites["enhancedUIPrompts"].battler)
          ret = 2
          break
        end
      elsif Input.trigger?(Input::JUMPUP) || Input.trigger?(Input::USE)
        ret = []
        if battler.opposes?
          ret.push(1)
          @battle.allOtherSideBattlers.reverse.each_with_index do |b, i| 
            next if b.index != battler.index
            ret.push(i)
          end
        else
          ret.push(0)
          @battle.allSameSideBattlers.each_with_index do |b, i| 
            next if b.index != battler.index
            ret.push(i)
          end
        end
        pbPlayDecisionSE
        break
      end
      if doFullRefresh
        battler = battlerTotal[idx]
        effects = pbGetDisplayEffects(battler)
        effctSize = effects.length - 1
        idxEffect = 0
        doRefresh = true
      end
      if doRefresh
        pbPlayCursorSE
        pbUpdateBattlerInfo(battler, effects, idxEffect)
        doRefresh = false
        doFullRefresh = false
      end
    end
    @sprites["leftarrow"].visible = false
    @sprites["rightarrow"].visible = false
    return ret
  end
  
  #-----------------------------------------------------------------------------
  # Draws the Battle Info UI.
  #-----------------------------------------------------------------------------
  def pbUpdateBattlerInfo(battler, effects, idxEffect = 0)
    @enhancedUIOverlay.clear
    pbUpdateBattlerIcons
    return if @enhancedUIToggle != :battler
    xpos = 28
    ypos = 24
    iconX = xpos + 28
    iconY = ypos + 62
    panelX = xpos + 240
    #---------------------------------------------------------------------------
    # General UI elements.
    poke = (battler.opposes?) ? battler.displayPokemon : battler.pokemon
    level = (battler.isRaidBoss?) ? "???" : battler.level.to_s
    movename = (battler.lastMoveUsed) ? GameData::Move.get(battler.lastMoveUsed).name : "---"
    movename = movename[0..12] + "..." if movename.length > 16
    imagePos = [
      [@path + "info_bg", 0, 0],
      [@path + "info_bg_data", 0, 0],
      [@path + "info_level", xpos + 16, ypos + 106]
    ]
    imagePos.push([@path + "info_gender", xpos + 148, ypos + 22, poke.gender * 22, 0, 22, 22]) if !battler.isRaidBoss?
    textPos  = [
      [_INTL("{1}", poke.name), iconX + 82, iconY - 20, :center, BASE_DARK, SHADOW_DARK],
      [_INTL("{1}", level), xpos + 38, ypos + 104, :left, BASE_LIGHT, SHADOW_LIGHT],
      [_INTL("Used: {1}", movename), xpos + 349, ypos + 104, :center, BASE_LIGHT, SHADOW_LIGHT],
      [_INTL("Turn {1}", @battle.turnCount + 1), Graphics.width - xpos - 32, ypos + 8, :center, BASE_DARK, SHADOW_DARK]
    ]
    #---------------------------------------------------------------------------
    # Battler icon.
    @battle.allBattlers.each do |b|
      @sprites["info_icon#{b.index}"].x = iconX
      @sprites["info_icon#{b.index}"].y = iconY
      @sprites["info_icon#{b.index}"].visible = (b.index == battler.index)
    end            
    #---------------------------------------------------------------------------
    # Owner
    if !battler.wild?
      imagePos.push([@path + "info_owner", xpos - 34, ypos + 6, 0, 20, 128, 20])
      textPos.push([@battle.pbGetOwnerFromBattlerIndex(battler.index).name, xpos + 32, ypos + 8, :center, BASE_DARK, SHADOW_DARK])
    end
    # Battler HP.
    if battler.hp > 0
      w = battler.hp * 96 / battler.totalhp.to_f
      w = 1 if w < 1
      w = ((w / 2).round) * 2
      hpzone = 0
      hpzone = 1 if battler.hp <= (battler.totalhp / 2).floor
      hpzone = 2 if battler.hp <= (battler.totalhp / 4).floor
      imagePos.push([@path + "info_hp", 86, 86, 0, hpzone * 6, w, 6])
    end
    # Battler status.
    if battler.status != :NONE
      iconPos = GameData::Status.get(battler.status).icon_position
      imagePos.push(["Graphics/UI/statuses", xpos + 86, ypos + 104, 0, iconPos * 16, 44, 16])
    end
    # Shininess
    imagePos.push(["Graphics/UI/shiny", xpos + 142, ypos + 102]) if poke.shiny?
    #---------------------------------------------------------------------------
    # Battler info for player-owned Pokemon.
    if battler.pbOwnedByPlayer?
      imagePos.push(
        [@path + "info_owner", xpos + 36, iconY + 10, 0, 0, 128, 20],
        [@path + "info_cursor", panelX, 62, 0, 0, 218, 26],
        [@path + "info_cursor", panelX, 86, 0, 0, 218, 26]
      )
      textPos.push(
        [_INTL("Abil."), xpos + 272, ypos + 44, :center, BASE_LIGHT, SHADOW_LIGHT],
        [_INTL("Item"), xpos + 272, ypos + 68, :center, BASE_LIGHT, SHADOW_LIGHT],
        [_INTL("{1}", battler.abilityName), xpos + 376, ypos + 44, :center, BASE_DARK, SHADOW_DARK],
        [_INTL("{1}", battler.itemName), xpos + 376, ypos + 68, :center, BASE_DARK, SHADOW_DARK],
        [sprintf("%d/%d", battler.hp, battler.totalhp), iconX + 74, iconY + 12, :center, BASE_LIGHT, SHADOW_LIGHT]
      )
    end
    #---------------------------------------------------------------------------
    pbAddWildIconDisplay(xpos, ypos, battler, imagePos)
    pbAddStatsDisplay(xpos, ypos, battler, imagePos, textPos)
    pbDrawImagePositions(@enhancedUIOverlay, imagePos)
    pbDrawTextPositions(@enhancedUIOverlay, textPos)
    pbAddTypesDisplay(xpos, ypos, battler, poke)
    pbAddEffectsDisplay(xpos, ypos, panelX, effects, idxEffect)
  end
  
  #-----------------------------------------------------------------------------
  # Draws additional icons on wild Pokemon to display cosmetic attributes.
  #-----------------------------------------------------------------------------
  def pbAddWildIconDisplay(xpos, ypos, battler, imagePos)
    return if !battler.wild?
    images = []
    pkmn = battler.pokemon
    #---------------------------------------------------------------------------
    # Checks if the wild Pokemon has at least one Shiny Leaf.
    if defined?(pkmn.shiny_leaf) && pkmn.shiny_leaf > 0
      images.push([Settings::POKEMON_UI_GRAPHICS_PATH + "leaf", 12, 10])
    end
    #---------------------------------------------------------------------------
    # Checks if the wild Pokemon's size is small or large.
    if defined?(pkmn.scale)
      case pkmn.scale
      when 0..59
        images.push([Settings::MEMENTOS_GRAPHICS_PATH + "size_icon", 6, 2, 0, 0, 28, 28])
      when 196..255
        images.push([Settings::MEMENTOS_GRAPHICS_PATH + "size_icon", 6, 4, 28, 0, 28, 28])
      end
    end
    #---------------------------------------------------------------------------
    # Checks if the wild Pokemon has a mark.
    if defined?(pkmn.memento) && pkmn.hasMementoType?(:mark)
      images.push([Settings::MEMENTOS_GRAPHICS_PATH + "memento_icon", 6, 4, 0, 0, 28, 28])
    end
    #---------------------------------------------------------------------------
    # Draws all cosmetic icons.
    if !images.empty?
      offset = images.length - 1
      baseX = xpos + 328 - offset * 26
      baseY = ypos + 42
      images.each_with_index do |img, i|
        imagePos.push([@path + "info_extra", baseX + (50 * i), baseY])
        img[1] += baseX + (50 * i)
        img[2] += baseY
        imagePos.push(img)
      end
    end
  end
  
  #-----------------------------------------------------------------------------
  # Draws the battler's stats and stat stages.
  #-----------------------------------------------------------------------------
  def pbAddStatsDisplay(xpos, ypos, battler, imagePos, textPos)
    [[:ATTACK,          _INTL("Attack")],
     [:DEFENSE,         _INTL("Defense")], 
     [:SPECIAL_ATTACK,  _INTL("Sp. Atk")], 
     [:SPECIAL_DEFENSE, _INTL("Sp. Def")], 
     [:SPEED,           _INTL("Speed")], 
     [:ACCURACY,        _INTL("Accuracy")], 
     [:EVASION,         _INTL("Evasion")],
     _INTL("Crit. Hit")
    ].each_with_index do |stat, i|
      if stat.is_a?(Array)
        color = SHADOW_LIGHT
        if battler.pbOwnedByPlayer?
          battler.pokemon.nature_for_stats.stat_changes.each do |s|
            if stat[0] == s[0]
              color = Color.new(136, 96, 72)  if s[1] > 0 # Red Nature text.
              color = Color.new(64, 120, 152) if s[1] < 0 # Blue Nature text.
            end
          end
        end
        textPos.push([stat[1], xpos + 16, ypos + 138 + (i * 24), :left, BASE_LIGHT, color])
        stage = battler.stages[stat[0]]
      else
        textPos.push([stat, xpos + 16, ypos + 138 + (i * 24), :left, BASE_LIGHT, SHADOW_LIGHT])
        stage = [battler.effects[PBEffects::FocusEnergy], 3].min
      end
      if stage != 0
        arrow = (stage > 0) ? 0 : 18
        stage.abs.times do |t| 
          imagePos.push([@path + "info_stats", xpos + 110 + (t * 18), ypos + 136 + (i * 24), arrow, 0, 18, 18])
        end
      end
    end
  end
  
  #-----------------------------------------------------------------------------
  # Draws the battler's typing.
  #-----------------------------------------------------------------------------
  def pbAddTypesDisplay(xpos, ypos, battler, poke)
    #---------------------------------------------------------------------------
    # Gets display types (considers Illusion)
    illusion = battler.effects[PBEffects::Illusion] && !battler.pbOwnedByPlayer?
    if battler.tera?
      displayTypes = (illusion) ? poke.types.clone : battler.pbPreTeraTypes
    elsif illusion
      displayTypes = poke.types.clone
      displayTypes.push(battler.effects[PBEffects::ExtraType]) if battler.effects[PBEffects::ExtraType]
    else
      displayTypes = battler.pbTypes(true)
    end
    #---------------------------------------------------------------------------
    # Displays the "???" type on newly encountered species, or battlers with no typing.
    if Settings::SHOW_TYPE_EFFECTIVENESS_FOR_NEW_SPECIES
      unknown_species = false
    else
      unknown_species = !(
        !@battle.internalBattle ||
        battler.pbOwnedByPlayer? ||
        $player.pokedex.owned?(poke.species) ||
        $player.pokedex.battled_count(poke.species) > 0
      )
    end
    displayTypes = [:QMARKS] if unknown_species || displayTypes.empty?
    #---------------------------------------------------------------------------
    # Draws each display type. Maximum of 3 types.
    typeY = (displayTypes.length >= 3) ? ypos + 6 : ypos + 34
    typebitmap = AnimatedBitmap.new(_INTL("Graphics/UI/types"))
    displayTypes.each_with_index do |type, i|
      break if i > 2
      type_number = GameData::Type.get(type).icon_position
      type_rect = Rect.new(0, type_number * 28, 64, 28)
      @enhancedUIOverlay.blt(xpos + 170, typeY + (i * 30), typebitmap.bitmap, type_rect)
    end
    #---------------------------------------------------------------------------
    # Draws Tera type.
    if battler.tera?
      showTera = true
    else
      showTera = defined?(battler.tera_type) && battler.pokemon.terastal_able?
      showTera = ((@battle.internalBattle) ? !battler.opposes? : true) if showTera
    end
    if showTera
      pkmn = (illusion) ? poke : battler
      pbDrawImagePositions(@enhancedUIOverlay, [[@path + "info_extra", xpos + 182, ypos + 95]])
      pbDisplayTeraType(pkmn, @enhancedUIOverlay, xpos + 186, ypos + 97, true)
    end
  end
  
  #-----------------------------------------------------------------------------
  # Draws the effects in play that are affecting the battler.
  #-----------------------------------------------------------------------------
  def pbAddEffectsDisplay(xpos, ypos, panelX, effects, idxEffect)
    return if effects.empty?
    idxLast = effects.length - 1
    offset = idxLast - 1
    if idxEffect < 4
      idxDisplay = idxEffect
    elsif [idxLast, offset].include?(idxEffect)
      idxDisplay = idxEffect
      idxDisplay -= 1 if idxDisplay == offset && offset < 5
    else
      idxDisplay = 3   
    end
    idxStart = (idxEffect > 3) ? idxEffect - 3 : 0
    if idxLast - idxEffect > 0
      idxEnd = idxStart + 4
    else
      idxStart = (idxLast - 4 > 0) ? idxLast - 4 : 0
      idxEnd = idxLast
    end
    textPos = []
    imagePos = [
      [@path + "info_effects", xpos + 240, ypos + 256],
      [@path + "info_slider_base", panelX + 222, ypos + 132]
    ]
    #---------------------------------------------------------------------------
    # Draws the slider.
    #---------------------------------------------------------------------------
    if effects.length > 5
      imagePos.push([@path + "info_slider", panelX + 222, ypos + 132, 0, 0, 18, 19]) if idxEffect > 3
      imagePos.push([@path + "info_slider", panelX + 222, ypos + 233, 0, 19, 18, 19]) if idxEffect < idxLast - 1
      sliderheight = 82
      boxheight = (sliderheight * 4 / idxLast).floor
      boxheight += [(sliderheight - boxheight) / 2, sliderheight / 4].min
      boxheight = [boxheight.floor, 18].max
      y = ypos + 152
      y += ((sliderheight - boxheight) * idxStart / (idxLast - 4)).floor
      imagePos.push([@path + "info_slider", panelX + 222, y, 18, 0, 18, 4])
      i = 0
      while i * 7 < boxheight - 2 - 7
        height = [boxheight - 2 - 7 - (i * 7), 7].min
        offset = y + 2 + (i * 7)
        imagePos.push([@path + "info_slider", panelX + 222, offset, 18, 2, 18, height])
        i += 1
      end
      imagePos.push([@path + "info_slider", panelX + 222, y + boxheight - 6 - 7, 18, 9, 18, 12])
    end
    #---------------------------------------------------------------------------
    # Draws each effect and the cursor.
    #---------------------------------------------------------------------------
    effects[idxStart..idxEnd].each_with_index do |effect, i|
      real_idx = effects.find_index(effect)
      if i == idxDisplay || idxEffect == real_idx
        imagePos.push([@path + "info_cursor", panelX, ypos + 132 + (i * 24), 0, 52, 218, 26])
        textPos.push([effect[0], xpos + 322, ypos + 138 + (i * 24), :center, BASE_LIGHT, SHADOW_LIGHT, :outline])
      else
        imagePos.push([@path + "info_cursor", panelX, ypos + 132 + (i * 24), 0, 26, 218, 26])
        textPos.push([effect[0], xpos + 322, ypos + 138 + (i * 24), :center, BASE_DARK, SHADOW_DARK])
      end
      textPos.push([effect[1], xpos + 426, ypos + 138 + (i * 24), :center, BASE_LIGHT, SHADOW_LIGHT])
    end
    pbDrawImagePositions(@enhancedUIOverlay, imagePos)
    pbDrawTextPositions(@enhancedUIOverlay, textPos)
    desc = effects[idxEffect][2]
    drawFormattedTextEx(@enhancedUIOverlay, xpos + 246, ypos + 266, 208, desc, BASE_DARK, SHADOW_DARK, 18)
  end
  
  #-----------------------------------------------------------------------------
  # Utility for getting an array of all effects that may be displayed.
  #-----------------------------------------------------------------------------
  def pbGetDisplayEffects(battler)
    display_effects = []
    #---------------------------------------------------------------------------
    # Damage gates for scripted battles.
    if battler.damageThreshold
      desc = _INTL("The Pokémon's HP won't fall below {1}% when attacked.", battler.damageThreshold)
      display_effects.push([_INTL("Damage Gate"), "--", desc])
    end
    #---------------------------------------------------------------------------
    # Special states.
    if battler.dynamax?
      if battler.effects[PBEffects::Dynamax] > 0 && !battler.isRaidBoss?
        tick = sprintf("%d/%d", battler.effects[PBEffects::Dynamax], Settings::DYNAMAX_TURNS)
      else
        tick = "--"
      end
      desc = _INTL("The Pokémon is in the Dynamax state.")
      display_effects.push([_INTL("Dynamax"), tick, desc])
    elsif battler.tera?
      data = GameData::Type.get(battler.tera_type).name
      desc = _INTL("The Pokémon is Terastallized into the {1} type.", data)
      display_effects.push([_INTL("Terastallization"), "--", desc])
    end
    #---------------------------------------------------------------------------
    # Weather
    weather = battler.effectiveWeather
    if weather != :None
      if weather == :Hail
        if defined?(Settings::HAIL_WEATHER_TYPE) && Settings::HAIL_WEATHER_TYPE > 0
          case Settings::HAIL_WEATHER_TYPE
          when 1
            name = _INTL("Snow")
            desc = _INTL("Boosts Def of Ice types. Blizzard always hits.")
          when 2
            name = _INTL("Hailstorm")
            desc = _INTL("Combined effects of both Hail and Snow.")
          end
        else
          name = GameData::BattleWeather.get(weather).name
          desc = _INTL("Non-Ice types take damage each turn. Blizzard always hits.")
        end
      else
        name = GameData::BattleWeather.get(weather).name
        case weather
        when :Sun         then desc = _INTL("Boosts Fire moves and weakens Water moves.")
        when :HarshSun    then desc = _INTL("Boosts Fire moves and negates Water moves.")
        when :Rain        then desc = _INTL("Boosts Water moves and weakens Fire moves.")
        when :HeavyRain   then desc = _INTL("Boosts Water moves and negates Fire moves.")
        when :Snow        then desc = _INTL("Boosts Def of Ice types. Blizzard always hits.")
        when :Sandstorm   then desc = _INTL("Boosts Rock type Sp. Def. Damages unless Rock/Ground/Steel.")
        when :StrongWinds then desc = _INTL("Flying types won't take super effective damage.")
        when :ShadowSky   then desc = _INTL("Boosts Shadow moves. Non-Shadow Pokémon damaged each turn.")
        else                   desc = _INTL("Unknown weather.")
        end
      end
      tick = (weather == @battle.field.weather) ? @battle.field.weatherDuration : 0
      tick = (tick > 0) ? sprintf("%d/%d", tick, 5) : "--"
      display_effects.push([name, tick, desc])
    end
    #---------------------------------------------------------------------------
    # Terrain
    if @battle.field.terrain != :None && battler.affectedByTerrain?
      name = _INTL("{1} Terrain", GameData::BattleTerrain.get(@battle.field.terrain).name)
      tick = @battle.field.terrainDuration
      tick = (tick > 0) ? sprintf("%d/%d", tick, 5) : "--"
      case @battle.field.terrain
      when :Electric then desc = _INTL("Grounded Pokémon immune to sleep. Boosts Electric moves.")
      when :Grassy   then desc = _INTL("Grounded Pokémon recover HP each turn. Boosts Grass moves.")
      when :Psychic  then desc = _INTL("Priority moves fail on grounded targets. Boosts Psychic moves.")
      when :Misty    then desc = _INTL("Status can't be changed when grounded. Weakens Dragon moves.")
	  else                desc = _INTL("Unknown terrain.")
      end
      display_effects.push([name, tick, desc])
    end
    #---------------------------------------------------------------------------
    # Battler effects that affect other Pokemon.
    if @battle.allBattlers.any? { |b| b.effects[PBEffects::Imprison] }
      name = GameData::Move.get(:IMPRISON).name
      desc = _INTL("Pokémon can't use moves known by an opposing {1} user.", name)
      display_effects.push([name, "--", desc])
    end
    if @battle.allBattlers.any? { |b| b.effects[PBEffects::Uproar] > 0 }
      name = GameData::Move.get(:UPROAR).name
      desc = _INTL("Pokémon cannot fall asleep during an uproar.")
      display_effects.push([name, "--", desc])
    end
    if @battle.allBattlers.any? { |b| b.effects[PBEffects::JawLock] == battler.index }
      name = _INTL("No Escape")
      desc = _INTL("The Pokémon can't flee or be switched out.")
      display_effects.push([name, "--", desc])
    end
    #---------------------------------------------------------------------------
    # All other effects.
    $DELUXE_PBEFFECTS.each do |key, key_hash|
      key_hash.each do |type, effects|
        effects.each do |effect|
          next if !PBEffects.const_defined?(effect)
          tick = "--"
          eff = PBEffects.const_get(effect)
          case key
          when :field    then value = @battle.field.effects[eff]
          when :team     then value = battler.pbOwnSide.effects[eff]
          when :position then value = @battle.positions[battler.index].effects[eff]
          when :battler  then value = battler.effects[eff]
          end
          case type
          when :boolean then next if !value
          when :counter then next if value == 0
          when :index   then next if value < 0
          end
          case effect
          #---------------------------------------------------------------------
          when :AquaRing
            name = GameData::Move.get(:AQUARING).name
            desc = _INTL("The Pokémon regains some HP at the end of each turn.")
          #---------------------------------------------------------------------
          when :Ingrain
            name = GameData::Move.get(:INGRAIN).name
            desc = _INTL("The Pokémon regains some HP every turn, but cannot switch out.")
          #---------------------------------------------------------------------
          when :LeechSeed
            name = GameData::Move.get(:LEECHSEED).name
            desc = _INTL("The Pokémon's HP is leeched every turn to heal {1}.", @battle.battlers[value].name)
          #---------------------------------------------------------------------
          when :Curse
            name = GameData::Move.get(:CURSE).name
            desc = _INTL("The Pokémon takes damage at the end of each turn.")
          #---------------------------------------------------------------------
          when :SaltCure
            name = GameData::Move.get(:SALTCURE).name
            desc = _INTL("The Pokémon takes damage at the end of each turn.")
          #---------------------------------------------------------------------
          when :Nightmare
            name = GameData::Move.get(:NIGHTMARE).name
            desc = _INTL("The Pokémon takes damage each turn it spends asleep.")
          #---------------------------------------------------------------------
          when :Rage
            name = GameData::Move.get(:RAGE).name
            desc = _INTL("The Pokémon's Attack stat increases whenever it's hit.")
          #---------------------------------------------------------------------
          when :HelpingHand
            name = GameData::Move.get(:HELPINGHAND).name
            desc = _INTL("The Pokémon's damage output is being increased.")
          #---------------------------------------------------------------------
          when :PowerTrick
            name = GameData::Move.get(:POWERTRICK).name
            desc = _INTL("The Pokémon's Atk and Def are swapped.")
          #---------------------------------------------------------------------
          when :Torment
            name = GameData::Move.get(:TORMENT).name
            desc = _INTL("The Pokémon can't use the same move twice in a row.")
          #---------------------------------------------------------------------
          when :Charge
            name = GameData::Move.get(:CHARGE).name
            desc = _INTL("The Pokémon's next Electric move will double in power.")
          #---------------------------------------------------------------------
          when :Electrify
            name = GameData::Move.get(:ELECTRIFY).name
            desc = _INTL("The Pokémon's next move will be Electric type.")
          #---------------------------------------------------------------------
          when :IonDeluge
            name = GameData::Move.get(:IONDELUGE).name
            desc = _INTL("The Pokémon's Normal type moves become Electric type.")
          #---------------------------------------------------------------------
          when :Minimize
            name = GameData::Move.get(:MINIMIZE).name
            desc = _INTL("The Pokémon shrunk and now takes more damage when squished.")
          #---------------------------------------------------------------------
          when :SkyDrop
            name = GameData::Move.get(:SKYDROP).name
            desc = _INTL("The Pokémon is being lifted in the air by {1}.", @battle.battlers[value].name)
          #---------------------------------------------------------------------
          when :TarShot
            name = GameData::Move.get(:TARSHOT).name
            desc = _INTL("The Pokémon has been made weaker to Fire type moves.")
          #---------------------------------------------------------------------
          when :Powder
            name = GameData::Move.get(:POWDER).name
            desc = _INTL("The Pokémon takes damage when it uses a Fire type move.")
          #---------------------------------------------------------------------
          when :Wish
            name = GameData::Move.get(:WISH).name
            desc = _INTL("The Pokémon in this spot restores HP on the next turn.")
          #---------------------------------------------------------------------
          when :HealingWish
            name = GameData::Move.get(:HEALINGWISH).name
            desc = _INTL("Fully heals a Pokémon switching into this spot.")
          #---------------------------------------------------------------------
          when :LunarDance
            name = GameData::Move.get(:LUNARDANCE).name
            desc = _INTL("Fully heals a Pokémon switching into this spot.")
          #---------------------------------------------------------------------
          when :Endure
            name = GameData::Move.get(:ENDURE).name
            desc = _INTL("The Pokémon will survive all incoming attacks with 1 HP.")
          #---------------------------------------------------------------------
          when :Substitute
            name = GameData::Move.get(:SUBSTITUTE).name
            desc = _INTL("The Pokémon's substitute will take any incoming moves.")
          #---------------------------------------------------------------------
          when :MagicCoat
            name = GameData::Move.get(:MAGICCOAT).name
            desc = _INTL("The Pokémon bounces back any incoming status moves.")
          #---------------------------------------------------------------------
          when :CraftyShield
            name = GameData::Move.get(:CRAFTYSHIELD).name
            desc = _INTL("The Pokémon is protected from all status moves.")
          #---------------------------------------------------------------------
          when :QuickGuard
            name = GameData::Move.get(:QUICKGUARD).name
            desc = _INTL("The Pokémon is protected from all priority moves.")
          #---------------------------------------------------------------------
          when :WideGuard
            name = GameData::Move.get(:WIDEGUARD).name
            desc = _INTL("The Pokémon is protected from all spread moves.")
          #---------------------------------------------------------------------
          when :Foresight
            name = GameData::Move.get(:FORESIGHT).name
            if battler.pbHasType?(:GHOST)
              desc = _INTL("The Pokémon's Ghost immunities and evasion boosts are ignored.")
            else
              desc = _INTL("The Pokémon's evasion boosts are ignored.")
            end
          #---------------------------------------------------------------------
          when :MiracleEye
            name = GameData::Move.get(:MIRACLEEYE).name
            if battler.pbHasType?(:DARK)
              desc = _INTL("The Pokémon's Dark immunities and evasion boosts are ignored.")
            else
              desc = _INTL("The Pokémon's evasion boosts are ignored.")
            end
          #---------------------------------------------------------------------
          when :SmackDown
            name = GameData::Move.get(:SMACKDOWN).name
            if battler.pbHasType?(:FLYING)
              desc = _INTL("The Pokémon is grounded and its Flying immunities are ignored.")
            else
              desc = _INTL("The Pokémon is grounded.")
            end
          #---------------------------------------------------------------------
          when :Stockpile
            name = GameData::Move.get(:STOCKPILE).name
            tick = sprintf("+%d", value)
            desc = _INTL("Stockpiling increases the Pokémon's defensive stats.")
          #---------------------------------------------------------------------
          when :Spikes
            name = GameData::Move.get(:SPIKES).name
            tick = sprintf("+%d", value)
            desc = _INTL("Grounded Pokémon that switch into battle will take damage.")
          #---------------------------------------------------------------------
          when :ToxicSpikes
            name = GameData::Move.get(:TOXICSPIKES).name
            tick = sprintf("+%d", value)
            desc = _INTL("Grounded Pokémon that switch into battle will be poisoned.")
          #---------------------------------------------------------------------
          when :StealthRock
            name = GameData::Move.get(:STEALTHROCK).name
            tick = _INTL("+1")
            desc = _INTL("Pokémon that switch into battle will take damage.")
          #---------------------------------------------------------------------
          when :Steelsurge
            name = GameData::Move.get(:GMAXSTEELSURGE).name
            tick = _INTL("+1")
            desc = _INTL("Pokémon that switch into battle will take damage.")
          #---------------------------------------------------------------------
          when :StickyWeb
            name = GameData::Move.get(:STICKYWEB).name
            tick = _INTL("+1")
            desc = _INTL("Pokémon that switch into battle will have their Speed lowered.")
          #---------------------------------------------------------------------
          when :LaserFocus
            name = GameData::Move.get(:LASERFOCUS).name
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("The Pokémon's next attack is a guaranteed critical hit.")
          #---------------------------------------------------------------------
          when :LockOn
            name = GameData::Move.get(:LOCKON).name
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("Any move used against a locked-on target will be sure to hit.")
          #---------------------------------------------------------------------
          when :ThroatChop
            name = GameData::Move.get(:THROATCHOP).name
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("The Pokémon can't use any sound-based moves.")
          #---------------------------------------------------------------------
          when :FairyLock
            name = GameData::Move.get(:FAIRYLOCK).name
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("No Pokémon can flee.")
          #---------------------------------------------------------------------
          when :Telekinesis
            name = GameData::Move.get(:TELEKINESIS).name
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon has been made airborne, but it cannot evade attacks.")
          #---------------------------------------------------------------------
          when :Encore
            name = GameData::Move.get(:ENCORE).name
            data = GameData::Move.get(battler.effects[PBEffects::EncoreMove]).name
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("Due to {1}, the Pokémon can only use {2}.", name, data)
          #---------------------------------------------------------------------
          when :Taunt
            name = GameData::Move.get(:TAUNT).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("The Pokémon can only use moves that deal damage.")
          #---------------------------------------------------------------------
          when :Tailwind
            name = GameData::Move.get(:TAILWIND).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("The Pokémon's Speed stat is doubled.")
          #---------------------------------------------------------------------
          when :VineLash
            name = GameData::Move.get(:GMAXVINELASH).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Pokémon that are not Grass types take damage every turn.")
          #---------------------------------------------------------------------
          when :Wildfire
            name = GameData::Move.get(:GMAXWILDFIRE).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Pokémon that are not Fire types take damage every turn.")
          #---------------------------------------------------------------------
          when :Cannonade
            name = GameData::Move.get(:GMAXCANNONADE).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Pokémon that are not Water types take damage every turn.")
          #---------------------------------------------------------------------
          when :Volcalith
            name = GameData::Move.get(:GMAXVOLCALITH).name
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Pokémon that are not Rock types take damage every turn.")
          #---------------------------------------------------------------------
          when :MagnetRise
            name = GameData::Move.get(:MAGNETRISE).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon is airborne and immune to Ground moves.")
          #---------------------------------------------------------------------
          when :HealBlock
            name = GameData::Move.get(:HEALBLOCK).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon's HP cannot be restored by healing effects.")
          #---------------------------------------------------------------------
          when :Embargo
            name = GameData::Move.get(:EMBARGO).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("Items cannot be used on or by the Pokémon.")
          #---------------------------------------------------------------------
          when :MudSport, :MudSportField
            name = GameData::Move.get(:MUDSPORT).name
            tick = sprintf("%d/%d", value, 5) if effect == :MudSportField
            desc = _INTL("The power of Electric moves is reduced.")
          #---------------------------------------------------------------------
          when :WaterSport, :WaterSportField
            name = GameData::Move.get(:WATERSPORT).name
            tick = sprintf("%d/%d", value, 5) if effect == :WaterSportField
            desc = _INTL("The power of Fire moves is reduced.")
          #---------------------------------------------------------------------
          when :AuroraVeil
            name = GameData::Move.get(:AURORAVEIL).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon takes half damage from physical and special moves.")
          #---------------------------------------------------------------------
          when :Reflect
            name = GameData::Move.get(:REFLECT).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon takes half damage from physical moves.")
          #---------------------------------------------------------------------
          when :LightScreen
            name = GameData::Move.get(:LIGHTSCREEN).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon takes half damage from special moves.")
          #---------------------------------------------------------------------
          when :Safeguard
            name = GameData::Move.get(:SAFEGUARD).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon is protected from status conditions.")
          #---------------------------------------------------------------------
          when :Mist
            name = GameData::Move.get(:MIST).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon's stats cannot be lowered.")
          #---------------------------------------------------------------------
          when :LuckyChant
            name = GameData::Move.get(:LUCKYCHANT).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("The Pokémon is immune to critical hits.")
          #---------------------------------------------------------------------
          when :Gravity
            name = GameData::Move.get(:GRAVITY).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("Grounds Pokémon. Prevents midair actions. Increases accuracy.")
          #---------------------------------------------------------------------
          when :MagicRoom
            name = GameData::Move.get(:MAGICROOM).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("No Pokémon can use their held items.")
          #---------------------------------------------------------------------
          when :WonderRoom
            name = GameData::Move.get(:WONDERROOM).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("All Pokémon swap their Def and Sp. Def stats.")
          #---------------------------------------------------------------------
          when :TrickRoom
            name = GameData::Move.get(:TRICKROOM).name
            tick = sprintf("%d/%d", value, 5)
            desc = _INTL("Slower Pokémon get to move first.")
          #---------------------------------------------------------------------
          when :Trapping
            name = _INTL("Bound")
            desc = _INTL("The Pokémon is bound and takes damage every turn.")
          #---------------------------------------------------------------------
          when :Toxic
            name = _INTL("Badly Poisoned")
            desc = _INTL("Damage the Pokémon takes from its poison worsens every turn.")
          #---------------------------------------------------------------------
          when :Confusion
            name = _INTL("Confusion")
            desc = _INTL("The Pokémon may hurt itself in its confusion.")
          #---------------------------------------------------------------------
          when :Outrage
            name = _INTL("Rampaging")
            desc = _INTL("The Pokémon rampages for 2-3 turns. It then becomes confused.")
          #---------------------------------------------------------------------
          when :GastroAcid
            name = _INTL("No Ability")
            desc = _INTL("The Pokémon's Ability loses its effect.")
          #---------------------------------------------------------------------
          when :FocusEnergy
            name = _INTL("Critical Hit Boost")
            desc = _INTL("The Pokémon is more likely to land critical hits.")
          #---------------------------------------------------------------------
          when :Attract
            name = _INTL("Infatuation")
            desc = _INTL("The Pokémon is less likely to attack {1}.", @battle.battlers[value].name)
          #---------------------------------------------------------------------
          when :WeightChange
            name = _INTL("Weight Changed")
            desc = _INTL("The Pokémon's weight has been {1}.", (value > 0) ? "increased" : "decreased")
          #---------------------------------------------------------------------
          when :MeanLook, :NoRetreat, :JawLock, :Octolock
            name = _INTL("No Escape")
            desc = _INTL("The Pokémon can't flee or be switched out.")
          #---------------------------------------------------------------------
          when :Protect, :SpikyShield, :BanefulBunker
            name = _INTL("Full Protect")
            desc = _INTL("The Pokémon is protected from all incoming moves.")
          #---------------------------------------------------------------------
          when :KingsShield, :Obstruct, :SilkTrap, :BurningBulwark, :MatBlock
            name = _INTL("Damage Protect")
            desc = _INTL("The Pokémon is protected from all incoming damage.")
          #---------------------------------------------------------------------
          when :ZHealing
            name = _INTL("Z-Healing")
            desc = _INTL("A Pokémon switching into this spot will recover its HP.")
          #---------------------------------------------------------------------
          when :TwoTurnAttack
            if battler.semiInvulnerable?
              name = _INTL("Semi-Invulnerable")
              desc = _INTL("The Pokémon cannot be hit by most attacks.")
            end
          #---------------------------------------------------------------------
          when :PerishSong
            name = _INTL("Counting Down")
            tick = value.to_s
            desc = _INTL("All Pokémon in this battle state will faint after 3 turns.")
          #---------------------------------------------------------------------
          when :FutureSightCounter
            name = _INTL("Future Attack")
            tick = value.to_s
            desc = _INTL("The Pokémon in this spot will be attacked in 2 turns.")
          #---------------------------------------------------------------------
          when :Syrupy
            name = _INTL("Speed Down")
            tick = value.to_s
            desc = _INTL("The Pokémon's Speed is lowered for 3 turns.", )
          #---------------------------------------------------------------------
          when :SlowStart
            name = GameData::Ability.get(:SLOWSTART).name
            tick = value.to_s
            desc = _INTL("The Pokémon gets its act together in 5 turns.")
          #---------------------------------------------------------------------
          when :Yawn
            name = _INTL("Drowsy")
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("The Pokémon will fall asleep at the end of the next turn.")
          #---------------------------------------------------------------------
          when :HyperBeam
            name = _INTL("Recharging")
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("The Pokémon cannot move until it recharges from its last attack.")
          #---------------------------------------------------------------------
          when :GlaiveRush
            name = _INTL("Vulnerable")
            tick = sprintf("%d/%d", value, 2)
            desc = _INTL("The Pokémon cannot evade and takes double damage.")
          #---------------------------------------------------------------------
          when :Splinters
            name = _INTL("Splinters")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon takes damage at the end of each turn.")
          #---------------------------------------------------------------------
          when :Disable
            name = _INTL("Move Disabled")
            data = GameData::Move.get(battler.effects[PBEffects::DisableMove]).name
            tick = sprintf("%d/%d", value, 4)
            desc =_INTL("{1} has been disabled and cannot be used.", data)
          #---------------------------------------------------------------------
          when :Rainbow
            name = _INTL("Rainbow")
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("The additional effects of moves are more likely to occur.")
          #---------------------------------------------------------------------
          when :Swamp
            name = _INTL("Swamp")
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Speed is reduced by 75% in swampy conditions.")
          #---------------------------------------------------------------------
          when :SeaOfFire
            name = _INTL("Sea of Fire")
            tick = sprintf("%d/%d", value, 4)
            desc = _INTL("Pokémon that are not Fire types take damage every turn.")
          #---------------------------------------------------------------------
          when :CheerOffense1
            name = _INTL("Offense Cheer 1")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon's attacks deal increased damage.")
          #---------------------------------------------------------------------
          when :CheerOffense2
            name = _INTL("Offense Cheer 2")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon's attacks will trigger effects & critically hit.")
          #---------------------------------------------------------------------
          when :CheerOffense3
            name = _INTL("Offense Cheer 3")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon's attacks bypass effects like Protect & Substitute.")
          #---------------------------------------------------------------------
          when :CheerDefense1
            name = _INTL("Defense Cheer 1")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon takes reduced damage from attacks.")
          #---------------------------------------------------------------------
          when :CheerDefense2
            name = _INTL("Defense Cheer 2")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon is immune to critical hits and move effects.")
          #---------------------------------------------------------------------
          when :CheerDefense3
            name = _INTL("Defense Cheer 3")
            tick = sprintf("%d/%d", value, 3)
            desc = _INTL("The Pokémon will survive all incoming attacks with 1 HP.")
          #---------------------------------------------------------------------
          else next
          end
          tick = "--" if type == :counter && value < 0
          display_effects.push([name, tick, desc])
        end
      end
    end
    display_effects.uniq!
    return display_effects
  end
end