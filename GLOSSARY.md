# Oracle of Music

Finds and displays the shortest chain of collaborations linking two music artists, in the spirit of the Oracle of Bacon.

## Language

**Artist**:
A musician or group that has credits on one or more Tracks.
_Avoid_: Band, performer

**Track**:
A recording credited to two or more Artists, which links those Artists to each other.
_Avoid_: Song, collab, recording

**Artist credit**:
The full credit line of a Track as published, which may name Artists not on the Path.
_Avoid_: Track artists, artists string

**Path**:
The full ordered chain from the start Artist to the end Artist, with each pair of neighbouring Artists joined by a Track.
_Avoid_: Connection, link, result

**Hop**:
One step of a Path: an Artist, the Track they share with the next Artist, and that next Artist.
_Avoid_: Connection, degree, edge

**Node**:
An Artist or Track as displayed on a Path.
_Avoid_: Vertex, circle, square

**Connector**:
The line drawn between an Artist Node and a Track Node when a Path is displayed.
_Avoid_: Connection, edge, line

**Legible**:
A displayed Path is legible when no Nodes or labels overlap and each one renders at or above a minimum readable size on the viewer's screen.
