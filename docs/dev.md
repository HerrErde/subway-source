# Dev Ramblings

(This text is not completely after checked.\
Some things may be wrong, missing or hard to understand.I don't care.)

(Some stuff where I tried to explain some the working (eventough i have absolutely no idea) or just some thing that I found interesting)

Info as of version 3.39.0\
While losing my mind tying to reverse-engineering the generic_challenges code

## Challenges

Challenges have different "Kinds"

1: Daily\
2: Meter\
3: ?\
4: City

in `rewardStates`\
the States are\
`0` not available to claim\
`1` able to claim\
`10` claimed

### Requirements

In save files are requirements that only allow the playing of a challenge with for example a specific character with a cooldown.\
apparently any can have a operator with recursively going lower

<details>

```json
"requirements": {
  "access": {
    "data": [
      {
        "type": "BaseMultiplier",
        "operator": "GreaterEqual",
        "value": "4"
      }
    ],
    "operator": "And"
  }
```

```json
"requirements": {
        "data":[{
          "operator":"GreaterEqual",
          "type":"AccountCreationTime",
          "value":"20"
        },
          {
            "operator":"Equal",
            "type":"HasInternet"
          }],
        "operator":"And"
      },
```

</details>

### Participation

participation of characters allowed in challenges\
with cost, ads, reuse time, key unlock

<details>

```json
"participation": {
"data": [
    {
    "type": "SelectedCharacter",
    "operator": "Equal",
    "value": "rudyrascal,buzz",
    "meta": {
        "items": [
        {
            "alternativeSkipCost": [
            {
                "adPlacement": "SkipCharacterCooldown",
                "currencyType": "Ads",
                "value": 1
            }
            ],
            "cooldown": 7200,
            "id": "rudyrascal",
            "limitRuns": 1,
            "skipCostKeys": [
            16
            ],
            "tryable": true
        },
        {
            "alternativeSkipCost": [
            {
                "adPlacement": "SkipCharacterCooldown",
                "currencyType": "Ads",
                "value": 1
            }
            ],
            "cooldown": 7200,
            "id": "buzz",
            "limitRuns": 1,
            "skipCostKeys": [
            16
            ]
        }
        ]
    }
    }
],
"operator": "And"
}
```

</details>

### Progress

```json
  "progress": {
    "data": [
      {
        "type": "City",
        "operator": "Equal",
        "value": "subwaycityfloorislava"
      }
    ],
    "operator": "And"
  }
}
```

### Operators

#### Types

Any\
GameCounts

#### Value

int in string

##### operator

And\
Or\
Equal

GreaterEqual\
LowerEqual

<details>

```json
{
  "type": "SelectedCharacter",
  "operator": "Equal",
  "value": "jake,tricky,fresh,yutani",
  "meta": {
    "items": [
      {
        "alternativeSkipCost": [],
        "cooldown": 7200,
        "id": "jake",
        "limitRuns": 1,
        "skipCostKeys": [16]
      }
    ]
  }
}
```

```json
"requirements": {
    "data":[{
        "operator":"GreaterEqual",
        "type":"AccountCreationTime",
        "value":"20"
    },
        {
        "operator":"Equal",
        "type":"HasInternet"
        }],
    "operator":"And"
    }
```

</details>

<p>
These have mostly meta data for their one option.
values show apparently the values that can be choosen with the items
items showing a more specified data overview of the settings
</p>
=======

here is a challenge from the file `generic_challenges.json`
in this state, which is sort of a level in the challenge, the reward requires an Ad set by the `AdRequired` key and cannot be collected without having to watch it

<details>

```json
"challengeStates": {
    "coinChallenge": {
    "challengeId": "coinChallenge",
    "rewardStates": [
        {
        "State": 10,
        "RequiredScore": 500,
        "AdRequired": true,
        "Rewards": [
            {
            "reward": {
                "type": "Currency",
                "id": "EventCoins",
                "value": 300
            },
            "fallbackReward": {
                "type": "Currency",
                "id": "Coins",
                "value": 300
            }
            }
        ]
        }
```

</details>

rewards are sorted into groups which begin from not set to 1\
for example 3 rewards then begins the next stage wich is then the next group

<details>

```json
"rewardStates": [
    {
    "State": 10,
    "RequiredScore": 250,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        }
    ]
    },
    {
    "State": 10,
    "RequiredScore": 500,
    "AdRequired": true,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        }
    ]
    },
    {
    "State": 10,
    "RequiredScore": 1000,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        },
        {
        "reward": {
        }
        }
    ]
    },
    {
    "State": 1,
    "RequiredScore": 2000,
    "GroupId": 1,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        }
    ]
    },
    {
    "State": 0,
    "RequiredScore": 3000,
    "GroupId": 1,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        },
        {
        "reward": {
        }
        }
    ]
    },
    {
    "State": 0,
    "RequiredScore": 4000,
    "GroupId": 2,
    "Rewards": [
        {
        "reward": {
        },
        "fallbackReward": {
        }
        }
    ]
    }
    ]
```

</details>
