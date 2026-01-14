#!/usr/bin/perl

use Digest::MD5 qw(md5_base64);
srand time();

$| = 1;

$input = 0;
$minDmg = $maxDmg = 50;
$mMinDmg = $mMaxDmg = 5;
$arm = $mArm = 5;
$crit = $mCrit = 1;
$life = 2500; $mLife = 500;
$gold = $mGold = 0;
$exp = $mExp = 0;
$cStr = 'gold';
$keys = 0;
@reqExp = (10,500,2500,4900,10000,16000,34000,80000,90000,100000,400000,800000,1000000,2000000,3000000);

$level = $mDifficulty = 1;
$mobType = 0;

$MENU_LABEL			= 0;
$MENU_ACTION		= 1;
$MENU_ACTION_ARGS	= 2;

$AFFIX_DETAIL	= 0;
$AFFIX_CODE		= 1;
$AFFIX_VALUE	= 2;

$FIGHT_STATUS_FIGHTING = 1;
$FIGHT_STATUS_MOB_DEAD = 4;
$FIGHT_STATUS_PLAYER_DEAD = 8;
$FIGHT_STATUS_ENDED = 2;
$FIGHT_STATUS_RAN = 16;

@equipTypes = ('boots','socks','tassets','belt','ring','necklace','bracelet','weapon','shield','hat');
%equipment = map { $_ => 0 } @equipTypes;

$MOB_NAME = 0;
$MOB_SPECIALS = 1;
$MOB_SPECIAL_DESC = 0;
$MOB_SPECIAL_CODE = 1;
@mobs = (
	['Mirror', [
		['Hit yourself for 50% HP', '$life -= ($life / 2)'], 
		['Hit yourself for 25% HP', '$life -= ($life / 4)'] ] ],
	['Clown', [
		['clowned around too much','$mLife -= 500000'], 
		['Scary, your chance of crit is temporarily ... 0%','$crit = 0'] ] ],
	['Bob', [
		['Steals all of your armor','$arm = 0'], 
		['Big Bob Hit! 1k damage','$life -= 1000'] ] ],
	['Zzzzzzz', [
		['Falls asleep and can no longer attack','$mMinDmg=0;$mMaxDmg=0'] ] ],
	['Joker', [
		['A funny catches you off guard, depleting 5000 life, probably killing y ou, maybe','$life -= 5000'] ] ],
	['SpearPerson', [
		['Launches a spear in your general direction causing probably 2k damage','$life -= 2000'] ] ]
);

@affixes = (
	['Adds 1-10 dmg', '$minDmg [OP] 1; $maxDmg [OP] 10;', 0],
	['Adds 5-10 dmg', '$minDmg [OP] 5; $maxDmg [OP] 10;', 1],
	['Adds 25 life', '$life [OP] 25', 10],
	['Adds 35 arm', '$arm [OP] 35', 15],
	['Adds 5 crit', '$crit [OP] 5', 10],
	['Adds 55 crit', '$crit [OP] 55', 480],
	['Adds 15 crit', '$crit [OP] 15', 30],
	['Adds 35-50 dmg', '$minDmg [OP] 35; $maxDmg [OP] 50;', 4],
	['Adds 25 crit', '$crit [OP] 25', 60],
	['Adds 45-62 dmg', '$minDmg [OP] 45; $maxDmg [OP] 62;', 5],
	['Adds 100 life', '$life [OP] 100', 50],
	['Adds 455 life', '$life [OP] 455', 120],
	['Adds 15-17 dmg', '$minDmg [OP] 15; $maxDmg [OP] 17;', 2],
	['Adds 115 arm', '$arm [OP] 115', 100],
	['Adds 165 arm', '$arm [OP] 165', 8],
	['Adds 35 crit', '$crit [OP] 35', 120],
	['Adds 45 crit', '$crit [OP] 45', 240],
	['Adds 322 life', '$life [OP] 322', 100],
	['Adds 1000 life', '$life [OP] 1000', 250],
	['Adds 95 crit', '$crit [OP] 55', 2000],
	['Adds 45 arm', '$arm [OP] 45', 17],
	['Adds 75 arm', '$arm [OP] 75', 20],
	['Adds 25-100 dmg', '$minDmg [OP] 25; $maxDmg [OP] 100;', 3],
	['Adds 115-150 dmg', '$minDmg [OP] 115; $maxDmg [OP] 150;', 25],
	['Adds 75-80 dmg', '$minDmg [OP] 75; $maxDmg [OP] 80;', 7],
	['Adds 95-192 dmg', '$minDmg [OP] 95; $maxDmg [OP] 192;', 20],
	['Adds 900 life', '$life [OP] 900', 200],
	['Adds 425 arm', '$arm [OP] 425', 200],
	['Adds 1115 arm', '$arm [OP] 1115', 300],
	['Adds 155-290 dmg', '$minDmg [OP] 155; $maxDmg [OP] 290;', 50],
	['Adds 155 crit', '$crit [OP] 55', 1480],
	['Adds 225 crit', '$crit [OP] 55', 4800],
	['Adds 225-600 dmg', '$minDmg [OP] 225; $maxDmg [OP] 600;', 100],
	['Adds 10000 life', '$life [OP] 10000', 500]
);
@affixRegex = (
	qr/ (\d+)-(\d+) (dmg)/,
	qr/ (\d+)( )(arm|crit|life)/
);
@highestAffix = (0,5,8,13,16,24,28,30,31,34);

# service defined output block
$s_out = "[wait]\n";
$e_out = "[/wait]\n";

# Save and load from this file
$DATA_DIR = "/var/data/rpg";
$username = $ARGV[0];
if (!$username) {
    print "Invalid username\n";
    exit 255;
}
if (-f "$DATA_DIR/$username") {
    _Load();
}

sub _LevelUp
{
	while ($exp > $reqExp[0])
	{
		print "! +level, you have gained an experience, this has happened $level times.\n";
		$level++;
		$exp -= $reqExp[0];
		push @reqExp, shift @reqExp;
	}
}

sub _RollItem
{
	my $maxAffixes = shift;
	my $type = shift || int rand scalar @equipTypes;
	my @a = ();
	my $value = 0;
	
	map { 
		my $aIndex;
		if (!$mDifficulty || $mDifficulty > 9)
		{
			$aIndex = int rand scalar @affixes;
		}
		else
		{
			$aIndex = int (rand $highestAffix[$mDifficulty]);
		}
		push @a, $aIndex;
		$value += $affixes[$aIndex][$AFFIX_VALUE];
	} (0..(int rand $maxAffixes) + 1);
	
	return {
		'type'		=> $equipTypes[$type],
		'affixes'	=> \@a,
		'value'		=> $value 
	};
}

sub _DisplayItem
{
	my $item = shift;
	print "\t", uc $item->{'type'}, " (", $item->{'value'}, "G)\n";
	print map { "\t\t".$affixes[$_][$AFFIX_DETAIL]."\n"; } @{$item->{'affixes'}};
}

sub _LootExplosion
{
	my $maxDrops = shift;
	for (0..int rand $maxDrops)
	{
		$item = _RollItem(int($mDifficulty / 2) + 3);
		if ($item->{'type'} ne 'gold')
		{
			_ItemQueryUser("Found Item", $item);
		}
		else
		{
			print "Found $item->{'value'} $cStr.\n";
			_AddGold($item);
		}
	}
}

sub _ItemQueryUser
{
	my $txt = shift;
	my $item = shift;

	print "$txt:\n";
	_DisplayItem($item);
		
	if ($equipment{$item->{'type'}})
	{
		print "Currently Equipped:\n";
		_DisplayItem($equipment{$item->{'type'}});
	}

	do {
		_QueryUser(
			[
				['Equip',\&_Equip,$item],
				['Sell',\&_AddGold,$item],
				['Show Gear',\&_DisplayGear]
			]
		);
	} while (!($input == 0 || $input == 1));
}

sub _DisplayStats
{
	my $type = shift;
	my $mode = shift;

	if ($type eq 'player')
	{
		if ($mode eq 'full')
		{
			my @data;
			my $tMin = 0;
			my $tMax = 0;
			my %totals = ('arm'=>0,'crit'=>0,'life'=>0);
			foreach my $eqType (@equipTypes)
			{
				my @stats = (0, 0, 0, 0);
				foreach my $affixId (@{$equipment{$eqType}->{'affixes'}})
				{
					foreach my $affixReg (@affixRegex)
					{
						if ($affixes[$affixId]->[$AFFIX_DETAIL] =~ /$affixReg/)
						{
							if ($3 eq 'dmg')
							{
								my $min = $1;
								my $max = $2;
								$tMin += $min;
								$tMax += $max;
								if ($stats[0] =~ /(\d+)-(\d+)/)
								{
									$min += $1;
									$max += $2;
								}
								$stats[0] = "$min-$max";
							}
							else
							{
								$stats[$3 eq 'arm' ? 1 : $3 eq 'crit' ? 2 : 3] += $1;
								$totals{$3} += $1;
							}
						}
					}
				}
				push @data, [ $eqType, "$stats[0]", "$stats[1]", "$stats[2]", "$stats[3]" ];
			}

			unshift @data, ["","dmg","arm","crit","life"];
			push @data , ["TOTALS","$tMin-$tMax","$totals{'arm'}","$totals{'crit'}","$totals{'life'}"];
			print "\tYOU (level $level, XP $exp/$reqExp[0])\n\t$cStr: $gold\n\tkeys: $keys\n";
			_OutputTable(\@data);
		
		}
		else
		{
			print "YOU (level $level, XP $exp/$reqExp[0]):\n\tArmor: $arm\n\tDamage: $minDmg - $maxDmg\n\tCrit: $crit\n\tLife: $life\n\t$cStr: $gold\n\tKeys:$keys\n";
		}
	}
	elsif ($type eq 'mob')
	{
		print "MOB:\n\ttype:$mobs[$mobType]->[$MOB_NAME]\n\tArmor: $mArm\n\tDamage: $mMinDmg - $mMaxDmg\n\tCrit: $mCrit\n\tLife: $mLife\n\t$cStr: $mGold\n";
	}
}

sub _OutputTable
{
	my $data = shift;
	my @columnSizes = ();

	foreach my $row (@$data)
	{
		my $i = 0;
		foreach my $col (@$row)
		{
			my $len = length($col);
			$columnSizes[$i] = $len if !exists $columnSizes[$i] || $len >= $columnSizes[$i];
			$i++;
		}
	}

	my $tableLen = (scalar (@columnSizes) * 4) + $#columnSizes;
	map { $tableLen += $_; } @columnSizes;
	
	print "\t+","-"x$tableLen,"+\n";
	my $j = 0;
	foreach $row (@$data)
	{
		my $i = 0;
		foreach $col (@$row)
		{
			print "\t" if $i == 0;
			my $spaces = $columnSizes[$i++] - length($col) + 4;
			my $odd = $spaces % 2 == 1 ? 1 : 0;
			$spaces-- if $odd;
			$spaces /= 2;
			
			print "+","-"x$tableLen,"+\n\t" if $col eq 'TOTALS';
			print "|"," "x$spaces,$odd ? " " : "",$col," "x$spaces;
		}
		print "|\n";
		print "\t+","-"x$tableLen,"+\n" if $j == 0;
		$j++;
	}
	print "\t+","-"x$tableLen,"+\n";
}

sub _Equip 
{ 
	my $item = shift;
	_AddGold($item->{'value'}) if $equipment{$item->{'type'}};
	$equipment{$item->{'type'}} = $item;
	_ModifyStats("+=", 'player');
}

sub _ApplyItemStats
{
	my $item	= shift;
	my $type	= shift;
	my $op		= shift;
	map { 
		my $code = $affixes[$_][$AFFIX_CODE];
		my %UC = ('a'=>'A','l'=>'L','c'=>'C','m'=>'M');
		$code =~ s/\[OP\]/$op/g;
		$code =~ s/\$([amcl])/\$m$UC{$1}/g if $type eq 'mob';
		eval $code;
	} @{$item->{'affixes'}} if $item;
}

sub _ModifyStats
{
	my $op		= shift;
	my $type	= shift;
	
	$minDmg = $maxDmg = 50;
	$arm = 5;
	$crit = 1;
	$life = 2500;
	foreach my $itemType (keys %equipment)
	{
		_ApplyItemStats($equipment{$itemType}, $type, $op);
	}
}

sub _QueryUser
{
	my $menu = shift;
	print "----------------------------\n";
	print map { ($_+1).") " . $menu->[$_][$MENU_LABEL] . "\n"; } 0..(scalar (@$menu) - 1);
	print "----------------------------\n";
	print "type /rpg #\n";
	$input = _GetInput();
	if ($input >= 0 && $input < scalar @$menu)
	{
		$menu->[$input][$MENU_ACTION]->($menu->[$input][$MENU_ACTION_ARGS]);
	}
	else
	{
        print "Invalid #\n";
		_QueryUser($menu);
		return;
	}
}

sub _GetInput
{
    print "[wait]\n";
	my $nodecr = shift;
	my $in = <STDIN>;
    if ($in eq "#sq\n") {
        # save quit!
        _Save();
        print "saved\n";
        exit(0);
    }
	$in =~ s/\s+$//;
	$in-- if !$nodecr;
	return $in;
}

sub _AddGold		{ $gold += shift->{'value'}; }
sub _Quit			{ _Save();print "[wait]\n"; exit 0; }
sub _SetMDifficulty	{ $mDifficulty = shift; }

sub _SpawnMob
{
	$mMinDmg = $mMaxDmg = 5;
	$mArm = 5;
	$mCrit = 1;
	$mLife = 500;
	$mGold = 0;
	$mExp = 0;
	$mobType = int rand scalar @mobs;
	for (0..$mDifficulty)
	{
		$item = _RollItem($mDifficulty);
		_ApplyItemStats($item, 'mob', '+=');
		$mExp += $item->{'value'};
	}
}

sub _Fight
{
	my $leaver = 0;
	my $fightStatus = $FIGHT_STATUS_FIGHTING;

	_QueryUser
	(
		[
			['Easiest',	\&_SetMDifficulty, 1],
			['Easier',	\&_SetMDifficulty, 2],
			['Easy', 	\&_SetMDifficulty, 3],
			['Normal',	\&_SetMDifficulty, 4],
			['Normal+',	\&_SetMDifficulty, 5],
			['Hard',	\&_SetMDifficulty, 6],
			['Hard++', 	\&_SetMDifficulty, 7],
			['Hard+++',	\&_SetMDifficulty, 9],
			['Insane',	\&_SetMDifficulty, 10],
			['Insane+',	\&_SetMDifficulty, 11],
			['Insane++',	\&_SetMDifficulty, 12]
		]
	);

	_SpawnMob();

	do {
		_DisplayStats('player');
		_DisplayStats('mob');
		_QueryUser
		(
			[
				['Run', 		\&_Run,		\$fightStatus],
				['Attack',		\&_Attack,	[\$fightStatus, 0]],
				['Auto Attack',	\&_Attack,	[\$fightStatus, 1]]
			]
		);
	} while ($fightStatus & $FIGHT_STATUS_FIGHTING);
	
	if ($fightStatus & $FIGHT_STATUS_MOB_DEAD)
	{
		$exp += $mExp;
		print "Vic! +$mExp XP (XP TOTAL: $exp), Looting...\n";
		_LevelUp();
		if (int rand(100) + 1 <= $mDifficulty*2)
		{
			print "You found a key, neat!\n";
			$keys++;
			print "Keys: $keys\n";
		}
		_LootExplosion($mDifficulty);
	}
	elsif ($fightStatus & $FIGHT_STATUS_PLAYER_DEAD)
	{
		print "You die, respawning...\n";
		print "Respawned, you keep all your gear and $cStr\n";
	}
	else
	{
		print "You rang. ran?.. you run away.\n";
	}
	_ModifyStats('+=','player');
}

sub _Attack
{
	my $args	= shift;
	my $fStatus	= $args->[0];
	my $isAuto	= $args->[1];

    #print "[sequence]\n" if $isAuto;
	do {

		_DisplayDamage
		(
			'You',
			'Mob',
			_Damage(\$mLife, $minDmg, $maxDmg, $crit, $mArm)
		);

		if ($mLife <= 0)
		{
			$$fStatus = $FIGHT_STATUS_ENDED | $FIGHT_STATUS_MOB_DEAD;
            #print "[/sequence]\n" if $isAuto;
			return;
		}

		if (int rand 100 <= 10)
		{
			print "$mobs[$mobType]->[$MOB_NAME] ";
			my $specialIdx = int rand scalar @{$mobs[$mobType]->[$MOB_SPECIALS]};
			print "$mobs[$mobType]->[$MOB_SPECIALS]->[$specialIdx]->[$MOB_SPECIAL_DESC]\n";
			eval $mobs[$mobType]->[$MOB_SPECIALS]->[$specialIdx]->[$MOB_SPECIAL_CODE];
			if ($mLife <= 0)
			{
				$$fStatus = $FIGHT_STATUS_ENDED | $FIGHT_STATUS_MOB_DEAD;
                #print "[/sequence]\n" if $isAuto;
				return;
			}
		}
		else
		{
			_DisplayDamage
			(
				'Mob',
				'You',
				_Damage(\$life, $mMinDmg, $mMaxDmg, $mCrit, $arm)
			);
		}
	
		if ($life <= 0)
		{
			$$fStatus = $FIGHT_STATUS_ENDED | $FIGHT_STATUS_PLAYER_DEAD;
            #print "[/sequence]\n" if $isAuto;
			return;
		}

        # TODO when sequencing is implemented per user.
		#select(undef,undef,undef,0.05);
	} while ($isAuto);
#    print "[/sequence]\n" if $isAuto;
}

sub _Damage
{
	my $targetLife = shift;
	my $attackerMinDmg = shift;
	my $attackerMaxDmg = shift;
	my $attackerCrit = shift;
	my $targetArm = shift;

	my $isCrit = 1;
	my $damage = 0;
	my $mitigated = 0;

	$attackerCrit *= 0.1;
	$attackerCrit = 1 if $attackerCrit < 1;

	$attackerCrit = int($attackerCrit) + 1;
	$attackerCrit = 100 if $attackerCrit > 100;

	$isCrit = 2 if (int rand (100)) < $attackerCrit;

	my $attackerDmg =
		((int rand ($attackerMaxDmg - $attackerMinDmg)) 
			+ $attackerMinDmg) * $isCrit;

	if ($targetArm >= 4500)
	{
		$mitigation = 0.45;
	}
	else
	{
		$mitigation = $targetArm / 4500;
	}

	$mitigated = int($attackerDmg * $mitigation);
	$damage = int($attackerDmg - $mitigated);
	$damage = 0 if $damage < 0;

	$$targetLife -= $damage;

	return ($isCrit == 2, $damage, $mitigated);
}

sub _DisplayDamage
{
	my $label	= shift;
	my $label1	= shift;
	my $isCrit	= shift;
	my $damage	= shift;
	my $miti	= shift;

	print $label;
	print $isCrit ? " crit " : " hit ";
	print "$label1 for $damage damage! ($miti mitigated)\n";
}

sub _Run
{
	my $status = shift;
	$$status = $FIGHT_STATUS_RAN;
}

sub _DisplayGear
{
	_DisplayStats('player', 'full');
}

sub _Gamble
{
	$mDifficulty = 0;
	_QueryUser
	(
		[
			["upto 4 Properties 100 $cStr", \&_Gamble_Item_Properties, 0],
			["upto 5 Properties 1000 $cStr", \&_Gamble_Item_Properties, 1],
			["upto 6 Properties 5000 $cStr", \&_Gamble_Item_Properties, 2],
			["upto 8 Properties 10000 $cStr, 2 keys", \&_Gamble_Item_Properties, 3],
			["upto 10 Properties 20000 $cStr, 5 keys", \&_Gamble_Item_Properties, 4],
			["upto 20 Properties 120000 $cStr, 25 keys", \&_Gamble_Item_Properties, 5]
		]
	);
}

sub _Gamble_Item_Properties
{
	my $idx = shift;
	my $i = 0;
	my @menu = map { [ $_, \&_Gamble_Item, [$idx, $i++] ] } @equipTypes;
	_QueryUser(\@menu);
}

sub _Gamble_Item
{
	my $args = shift;
	my $costIdx = $args->[0];
	my $itemType = $args->[1];
	my $cost = [
		[100, 0, 4],
		[1000, 0, 5],
		[5000, 0, 6],
		[10000, 2, 8],
		[20000, 5, 10],
		[120000, 25, 20]
	];

	if ($cost->[$costIdx]->[0] <= $gold &&
		$cost->[$costIdx]->[1] <= $keys)
	{
		my $item = _RollItem($cost->[$costIdx]->[2], $itemType);
		_ItemQueryUser("Gambled Item", $item);
		$gold -= $cost->[$costIdx]->[0];
		$keys -= $cost->[$costIdx]->[1];
	}
	else
	{
		print "Not enough money or keys.\n";
	}
}

# lol! what is this
sub _Save
{
	#my $name = _GetInput(1);
	# this is the now the username from thingbyb.
    my $name = $username;

	my $data = hex($gold).",".hex($keys).",".hex($level).",".hex($exp)."\n";
	$data .= "\%equipment = (";
	foreach my $equip (keys %equipment)
	{
		if ($equipment{$equip})
		{
			my $item = $equipment{$equip};
			my $type = $item->{'type'};
			my $affixes = join ",", @{$item->{'affixes'}};
			my $value = $item->{'value'};
			$data .= "'$equip'=>{'type'=>'$type','affixes'=>[$affixes],'value'=>$value},";
		}
	}
	$data .= ");";

	$data =~ s/(.)/sprintf '%02x',ord $1 /seg;
	my $md5 = md5_base64($data);
	open(FH, "> $DATA_DIR/$name") or die $!;
	print FH $data, "\n", $md5;
	close FH;
}

sub _Load
{
	#my $name = _GetInput(1);
	# this is the now the username from thingbyb.
    my $name = $username;
	my $buffer;
	{
		local $/ = undef;
		if( open(FH, "< $DATA_DIR/$name"))
		{
			$buffer = <FH>;
			close FH;
		}
	}
	my ($data, $md5) = split /\n/,$buffer;
	my $md5_test = md5_base64($data);
	if ($md5 ne $md5_test)
	{
		print "Save file was modified, big oh no!\n";
		return;
	}
	$data =~ s/([a-fA-F0-9]{2})/chr(hex($1))/eg;
	my @arr = split /\n/, $data;
	if ($arr[0] =~ /(\d+),(\d+),(\d+),(\d+)/)
	{
		$gold = $1;
		$keys = $2;
		$level = $3;
		$exp = $4;
        if ($level >= $#reqExp) {
            $level = $#reqExp - 1;
        }
		for (1..$level)
		{
			push @reqExp, shift @reqExp;
		}
	}
	eval $arr[1];
	_ModifyStats("+=","player");
	_DisplayGear();
}

sub _BuildMainMenu
{
	my @menu = ();

	push @menu, ['Fight', 		\&_Fight];
	push @menu, ['Show Stats',	\&_DisplayGear];
	push @menu, ['Gamble',		\&_Gamble];
	push @menu, ['Save',		\&_Save];
	push @menu, ['Load',		\&_Load];
	push @menu, ['Save & Quit',	\&_Quit];
	return \@menu;
}

my $mainMenu = _BuildMainMenu();
print "$username loaded.\n";
do {
	_QueryUser($mainMenu);
} while(1);

1;
